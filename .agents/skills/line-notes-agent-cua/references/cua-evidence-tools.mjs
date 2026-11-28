// Single implementation source for the notes CUA evidence helper. The documented
// loader imports this module and calls createEvidenceTools(cua) with the current
// CUA handle provider; importing this module or creating the tools never calls CUA.
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import { Buffer } from 'node:buffer';
import { createHash } from 'node:crypto';
import { types as utilTypes } from 'node:util';

export function createEvidenceTools(cua) {
  function describeError(error) {
    return {
      name: error && typeof error.name === 'string' ? error.name : 'UNKNOWN',
      code: error && typeof error.code === 'string' ? error.code : 'UNKNOWN',
      message: String(error && error.message ? error.message : error).slice(0, 500),
    };
  }

  function sha256(bytes) {
    return createHash('sha256').update(bytes).digest('hex');
  }

  function copyExactUint8Array(value) {
    try {
      if (!utilTypes.isUint8Array(value)) {
        return { ok: false, reason: 'NOT_UINT8ARRAY' };
      }
      const bytes = Buffer.allocUnsafe(value.byteLength);
      bytes.set(new Uint8Array(value.buffer, value.byteOffset, value.byteLength));
      return { ok: true, bytes };
    } catch (error) {
      return { ok: false, reason: 'VIEW_COPY_FAILED', error: describeError(error) };
    }
  }

  function normalizeHostCalls(hostCalls, timeKeys) {
    const value = hostCalls !== null && typeof hostCalls === 'object' ? hostCalls : {};
    const normalized = {};
    for (const key of timeKeys) {
      normalized[key] = typeof value[key] === 'string' ? value[key] : 'NOT_RUN';
    }
    normalized.clock_source = 'HOST_JS_DATE';
    normalized.precision = 'CALL_BOUNDARY_ONLY';
    normalized.os_event_time = 'UNKNOWN';
    return normalized;
  }

  async function writeExclusive(filePath, bytes) {
    try {
      await fs.writeFile(filePath, bytes, { flag: 'wx', mode: 0o600 });
      return { status: 'WRITTEN' };
    } catch (error) {
      return { status: 'FAILED', error: describeError(error) };
    }
  }

  async function readbackExact(filePath, expectedBytes) {
    try {
      const saved = await fs.readFile(filePath);
      const expected_sha256 = sha256(expectedBytes);
      const saved_sha256 = sha256(saved);
      return {
        status: saved.length === expectedBytes.length &&
                saved_sha256 === expected_sha256 ? 'MATCH' : 'MISMATCH',
        expected_bytes: expectedBytes.length,
        saved_bytes: saved.length,
        expected_sha256,
        saved_sha256,
      };
    } catch (error) {
      return {
        status: 'FAILED',
        expected_bytes: expectedBytes.length,
        expected_sha256: sha256(expectedBytes),
        error: describeError(error),
      };
    }
  }

  async function persistAsset(metadata, role, filePath, bytes) {
    const asset = {
      path: filePath,
      bytes: bytes.length,
      sha256: sha256(bytes),
      write: 'NOT_RUN',
      readback: 'NOT_RUN',
    };
    metadata.assets[role] = asset;
    const write = await writeExclusive(filePath, bytes);
    asset.write = write.status;
    if (write.error) asset.write_error = write.error;
    if (write.status !== 'WRITTEN') return false;
    const readback = await readbackExact(filePath, bytes);
    asset.readback = readback.status;
    asset.saved_bytes = readback.saved_bytes;
    asset.saved_sha256 = readback.saved_sha256;
    if (readback.error) asset.readback_error = readback.error;
    return readback.status === 'MATCH';
  }

  async function validatePrivatePaths(taskDir, observationDir) {
    try {
      if (!path.isAbsolute(taskDir) || !path.isAbsolute(observationDir)) {
        return { ok: false, error: { code: 'ABSOLUTE_PATH_REQUIRED' } };
      }
      const taskReal = await fs.realpath(taskDir);
      const observationReal = await fs.realpath(observationDir);
      if (path.resolve(taskDir) !== taskReal ||
          path.resolve(observationDir) !== observationReal) {
        return { ok: false, error: { code: 'CANONICAL_PRIVATE_PATH_REQUIRED' } };
      }
      if (observationReal === taskReal ||
          !observationReal.startsWith(taskReal + path.sep)) {
        return { ok: false, error: { code: 'PRIVATE_TASK_SUBDIRECTORY_REQUIRED' } };
      }
      return { ok: true, task_dir: taskReal, observation_dir: observationReal };
    } catch (error) {
      return { ok: false, error: describeError(error) };
    }
  }

  function isAxNoChangeStub(stateText) {
    if (typeof stateText !== 'string') return false;
    const trimmed = stateText.trim();
    if (!trimmed || trimmed.length > 512) return false;
    const lines = trimmed.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    if (lines.length === 0 || lines.length > 3) return false;
    if (!/^There has been no change in the accessibility tree\b/i.test(lines[0])) {
      return false;
    }
    return lines.slice(1).every(line => !/^\d+\s+/.test(line));
  }

  async function persistObservation(options) {
    const metadata = {
      schema_version: 1,
      observation_id: options.observationId,
      created_at: {
        value: new Date().toISOString(),
        source: 'CUA Node runtime Date',
      },
      task_dir: options.taskDir,
      observation_dir: options.observationDir,
      files: {
        ax: path.join(options.observationDir, options.observationId + '.ax.txt'),
        screenshot: path.join(options.observationDir,
                              options.observationId + '.screenshot.bin'),
        diagnostic: path.join(options.observationDir,
                              options.observationId + '.diagnostic.json'),
      },
      stages: {},
      assets: {},
      hostCalls: normalizeHostCalls(options.hostCalls, [
        'capture_call_started_at', 'capture_call_returned_at',
      ]),
      ready_for_bind: false,
      blockers: [],
    };
    const setStage = (name, status, detail) => {
      metadata.stages[name] = Object.assign({ status }, detail || {});
    };
    const result = (blockers, readyForBind = false) => Object.assign({
      ready_for_bind: false,
      blockers,
      observation_id: options.observationId,
      files: metadata.files,
    }, metadata, {
      ready_for_bind: readyForBind,
      blockers: [...blockers],
    });

    if (typeof options.observationId !== 'string' ||
        !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(options.observationId)) {
      setStage('OBSERVATION_ID', 'INVALID');
      return result(['OBSERVATION_ID:INVALID']);
    }
    setStage('OBSERVATION_ID', 'OK');

    const paths = await validatePrivatePaths(options.taskDir, options.observationDir);
    if (!paths.ok) {
      setStage('PRIVATE_PATHS', 'FAILED', { error: paths.error });
      return result(['PRIVATE_PATHS:FAILED']);
    }
    setStage('PRIVATE_PATHS', 'OK');

    const hasCaptureBoundary = key => {
      const value = metadata.hostCalls[key];
      return typeof value === 'string' && value.trim().length > 0 &&
        value !== 'NOT_RUN' && value !== 'UNKNOWN';
    };
    setStage(
      'CAPTURE_BOUNDARY',
      hasCaptureBoundary('capture_call_started_at') &&
        hasCaptureBoundary('capture_call_returned_at')
        ? 'RECORDED' : 'MISSING',
    );

    const capture = options.capture;
    const blockers = [];
    if (options.captureError) {
      setStage('CAPTURE', 'FAILED', { error: options.captureError });
      blockers.push('CAPTURE:FAILED');
    } else if (!capture || typeof capture !== 'object' || Array.isArray(capture)) {
      setStage('CAPTURE', 'FAILED', { error: { code: 'CAPTURE_SHAPE_INVALID' } });
      blockers.push('CAPTURE:FAILED');
    } else {
      setStage('CAPTURE', 'OK');
      if (capture.regions !== undefined && capture.regions !== null) {
        setStage('CAPTURE_SHAPE', 'UNSUPPORTED_REGIONS');
        blockers.push('CAPTURE_SHAPE:UNSUPPORTED_REGIONS');
      } else {
        setStage('CAPTURE_SHAPE', 'SUPPORTED_SINGLE_SCREENSHOT');
      }
    }

    let axBytes = null;
    if (capture && typeof capture.state === 'string') {
      if (capture.state.trim().length === 0) {
        setStage('AX', 'EMPTY');
        blockers.push('AX:EMPTY');
      } else if (isAxNoChangeStub(capture.state)) {
        // A no-change line is a diff notification, not a usable tree. Keep the
        // raw bytes for read-only diagnosis but fail closed for bind/download.
        axBytes = Buffer.from(capture.state, 'utf8');
        setStage('AX', 'DIFF_NO_CHANGE', {
          utf8_bytes: axBytes.length,
          full_tree: false,
          diff_only: true,
          stale_index_warning: true,
        });
        blockers.push('AX:DIFF_NO_CHANGE');
      } else {
        axBytes = Buffer.from(capture.state, 'utf8');
        setStage('AX', 'OK', {
          utf8_bytes: axBytes.length,
          full_tree: true,
          diff_only: false,
        });
      }
    } else if (capture) {
      setStage('AX', 'INVALID_TYPE',
               { observed_type: capture.state === null ? 'null' : typeof capture.state });
      blockers.push('AX:INVALID_TYPE');
    } else {
      setStage('AX', 'NOT_AVAILABLE');
    }

    let screenshotBytes = null;
    if (capture) {
      const copied = copyExactUint8Array(capture.screenshot);
      if (!copied.ok && copied.reason === 'NOT_UINT8ARRAY') {
        setStage('SCREENSHOT_TYPE', 'INVALID_TYPE');
        blockers.push('SCREENSHOT_TYPE:INVALID_TYPE');
      } else if (!copied.ok) {
        setStage('SCREENSHOT_TYPE', 'COPY_FAILED', { error: copied.error });
        blockers.push('SCREENSHOT_TYPE:COPY_FAILED');
      } else {
        setStage('SCREENSHOT_TYPE', 'OK');
        if (copied.bytes.length === 0) {
          setStage('SCREENSHOT_LENGTH', 'EMPTY');
          blockers.push('SCREENSHOT_LENGTH:EMPTY');
        } else {
          screenshotBytes = copied.bytes;
          setStage('SCREENSHOT_LENGTH', 'OK',
                   { bytes: screenshotBytes.length });
        }
      }
    } else {
      setStage('SCREENSHOT_TYPE', 'NOT_AVAILABLE');
      setStage('SCREENSHOT_LENGTH', 'NOT_AVAILABLE');
    }

    if (axBytes !== null) {
      if (await persistAsset(metadata, 'ax', metadata.files.ax, axBytes)) {
        setStage('AX_PERSISTENCE', 'MATCH');
      } else {
        setStage('AX_PERSISTENCE', 'FAILED');
        blockers.push('AX_PERSISTENCE:FAILED');
      }
    } else {
      setStage('AX_PERSISTENCE', 'SKIPPED');
    }

    if (screenshotBytes !== null) {
      if (await persistAsset(metadata, 'screenshot', metadata.files.screenshot,
                             screenshotBytes)) {
        setStage('SCREENSHOT_PERSISTENCE', 'MATCH');
      } else {
        setStage('SCREENSHOT_PERSISTENCE', 'FAILED');
        blockers.push('SCREENSHOT_PERSISTENCE:FAILED');
      }
    } else {
      setStage('SCREENSHOT_PERSISTENCE', 'SKIPPED');
    }

    metadata.ready_for_bind = blockers.length === 0;
    metadata.blockers = [...blockers];
    const diagnosticBytes = Buffer.from(JSON.stringify(metadata, null, 2) + '\n', 'utf8');
    const diagnosticWrite = await writeExclusive(metadata.files.diagnostic,
                                                  diagnosticBytes);
    const diagnostic = {
      path: metadata.files.diagnostic,
      bytes: diagnosticBytes.length,
      sha256: sha256(diagnosticBytes),
      write: diagnosticWrite.status,
      readback: 'NOT_RUN',
    };
    if (diagnosticWrite.error) diagnostic.write_error = diagnosticWrite.error;
    if (diagnosticWrite.status === 'WRITTEN') {
      const readback = await readbackExact(metadata.files.diagnostic, diagnosticBytes);
      diagnostic.readback = readback.status;
      diagnostic.saved_bytes = readback.saved_bytes;
      diagnostic.saved_sha256 = readback.saved_sha256;
      if (readback.error) diagnostic.readback_error = readback.error;
    }
    if (diagnostic.write !== 'WRITTEN' || diagnostic.readback !== 'MATCH') {
      blockers.push('DIAGNOSTIC_PERSISTENCE:FAILED');
    }

    const output = result(blockers, blockers.length === 0);
    output.metadata_persistence = diagnostic;
    output.ready_for_bind = blockers.length === 0;
    return output;
  }

  function inputErrorSnapshot(error) {
    const objectLike = error !== null &&
      (typeof error === 'object' || typeof error === 'function');
    const value = objectLike ? error : { value: error };
    const ownFields = Object.create(null);
    let fieldsComplete = true;
    let ownNames = [];
    const fieldGaps = [];
    try {
      ownNames = Object.getOwnPropertyNames(value);
    } catch (captureError) {
      fieldsComplete = false;
      fieldGaps.push('STRING_OWN_KEYS_CAPTURE_FAILED');
    }
    try {
      const ownSymbols = Object.getOwnPropertySymbols(value);
      if (ownSymbols.length > 0) {
        fieldsComplete = false;
        fieldGaps.push('SYMBOL_KEYED_OWN_FIELDS_UNCAPTURED:' + ownSymbols.length);
      }
    } catch (captureError) {
      fieldsComplete = false;
      fieldGaps.push('SYMBOL_OWN_KEYS_CAPTURE_FAILED');
    }
    for (const key of ownNames) {
      try {
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (descriptor && Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
          ownFields[key] = descriptor.value;
        } else {
          fieldsComplete = false;
          ownFields[key] = '[ACCESSOR_NOT_CAPTURED]';
        }
      } catch (captureError) {
        fieldsComplete = false;
        ownFields[key] = '[FIELD_CAPTURE_FAILED]';
      }
    }
    let name = 'UNKNOWN';
    let message;
    let code = null;
    try {
      if (typeof value.name === 'string') name = value.name;
      if (typeof value.message === 'string') message = value.message;
      else message = String(error);
      if (value.code !== undefined) code = value.code;
    } catch (captureError) {
      fieldsComplete = false;
      message = '[ERROR_MESSAGE_READ_FAILED]';
    }
    return { name, message, code, own_fields: ownFields,
             fields_complete: fieldsComplete, field_gaps: fieldGaps };
  }

  function inputErrorSummary(snapshot) {
    const code = snapshot.code;
    return {
      name: snapshot.name,
      message: snapshot.message,
      code: code === null || ['string', 'number', 'boolean'].includes(typeof code)
        ? code : '[NON_SCALAR_CODE]',
      own_field_names: Object.keys(snapshot.own_fields || {}),
      fields_complete: snapshot.fields_complete,
      field_gaps: snapshot.field_gaps || [],
    };
  }

  function jsonSerializationGap(value, ancestors = new Set(), location = '$') {
    const kind = typeof value;
    if (value === null || kind === 'string' || kind === 'boolean') return null;
    if (kind === 'number') return Number.isFinite(value) ? null : location + ':NON_FINITE_NUMBER';
    if (kind === 'undefined' || kind === 'function' || kind === 'symbol' || kind === 'bigint') {
      return location + ':UNSUPPORTED_' + kind.toUpperCase();
    }
    if (kind !== 'object') return location + ':UNSUPPORTED_VALUE';
    if (ancestors.has(value)) return location + ':CIRCULAR_REFERENCE';
    const array = Array.isArray(value);
    const prototype = Object.getPrototypeOf(value);
    if (!array && prototype !== Object.prototype && prototype !== null) {
      return location + ':NON_PLAIN_OBJECT';
    }
    ancestors.add(value);
    try {
      for (const key of Reflect.ownKeys(value)) {
        if (typeof key === 'symbol') return location + ':SYMBOL_KEY';
        if (array && key === 'length') continue;
        const descriptor = Object.getOwnPropertyDescriptor(value, key);
        if (!descriptor || !descriptor.enumerable) return location + '.' + key + ':NON_ENUMERABLE';
        if (!Object.prototype.hasOwnProperty.call(descriptor, 'value')) {
          return location + '.' + key + ':ACCESSOR_PROPERTY';
        }
        const gap = jsonSerializationGap(descriptor.value, ancestors, location + '.' + key);
        if (gap) return gap;
      }
      if (array) {
        for (let index = 0; index < value.length; index += 1) {
          if (!Object.prototype.hasOwnProperty.call(value, index)) {
            return location + '[' + index + ']:SPARSE_ARRAY_SLOT';
          }
        }
      }
      return null;
    } finally {
      ancestors.delete(value);
    }
  }

  function snapshotJsonValue(value) {
    try {
      const gap = jsonSerializationGap(value);
      if (gap) {
        return { ok: false, code: 'JSON_COMPLETENESS_REQUIRED', detail: gap };
      }
      const text = JSON.stringify(value);
      if (typeof text !== 'string') {
        return { ok: false, code: 'JSON_SERIALIZATION_FAILED' };
      }
      return { ok: true, value: JSON.parse(text) };
    } catch (error) {
      return {
        ok: false,
        code: 'JSON_SERIALIZATION_FAILED',
        error: inputErrorSnapshot(error),
      };
    }
  }

  const groundedDispatchToken = Object.freeze({});

  function syncGroundedDispatch(output, dispatchContext) {
    if (!dispatchContext || dispatchContext.token !== groundedDispatchToken) {
      return;
    }
    if (dispatchContext.dispatch) {
      output.dispatch_call_target = dispatchContext.dispatch.call_target;
      output.native_return_type = dispatchContext.dispatch.return_type;
    }
    output.native_dispatched_target = 'UNKNOWN';
    output.receipt_target_match = 'UNKNOWN';
    output.receipt_is_os_event_trace = false;
    if (dispatchContext.sourceObservationReadback) {
      output.source_observation_readback =
        dispatchContext.sourceObservationReadback;
    }
    if (dispatchContext.mappingEvidenceReadback) {
      output.mapping_evidence_readback =
        dispatchContext.mappingEvidenceReadback;
    }
    if (dispatchContext.hostCalls) {
      output.hostCalls = normalizeHostCalls(dispatchContext.hostCalls, [
        'dispatch_call_started_at', 'dispatch_call_returned_at',
      ]);
    }
  }

  async function persistSingleInput(options) {
    if (!options || typeof options !== 'object') {
      return {
        schema: 'line-notes-single-input/v1',
        operation_id: 'UNKNOWN',
        status: 'INVALID_HELPER_ARGUMENTS',
        blockers: ['OPTIONS_REQUIRED'],
        request: { status: 'NOT_RUN' },
        raw_return: { status: 'NOT_RUN', complete: false },
        diagnostic: { status: 'NOT_RUN', complete: false },
        files: {},
        receipt_is_os_event_trace: false,
      };
    }
    if (options.request &&
        (options.request.input_phase === 'DOWNLOAD_CONTROL' ||
         options.request.phase === 'DOWNLOAD_CONTROL')) {
      return {
        schema: 'line-notes-single-input/v1',
        operation_id: options.operationId || 'UNKNOWN',
        status: 'DOWNLOAD_CONTROL_REQUIRES_GROUNDED_HELPER',
        blockers: ['DOWNLOAD_CONTROL_REQUIRES_GROUNDED_HELPER'],
        request: { status: 'NOT_RUN' },
        raw_return: { status: 'NOT_RUN', complete: false },
        diagnostic: { status: 'NOT_RUN', complete: false },
        files: {},
        receipt_is_os_event_trace: false,
      };
    }
    return persistSingleInputInternal(options);
  }

  async function persistSingleInputInternal(options, dispatchContext = null) {
    const grounded = Boolean(dispatchContext &&
      dispatchContext.token === groundedDispatchToken);
    const validId = typeof options.operationId === 'string' &&
      /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(options.operationId);
    const output = {
      schema: grounded
        ? 'line-notes-grounded-download-click/v1'
        : 'line-notes-single-input/v1',
      operation_id: options.operationId || 'UNKNOWN',
      status: 'NOT_INVOKED',
      request: { status: 'NOT_RUN' },
      raw_return: { status: 'NOT_RUN', complete: false },
      diagnostic: { status: 'NOT_RUN', complete: false },
      files: {},
      receipt_is_os_event_trace: false,
    };
    if (grounded) {
      output.source_observation_readback = { status: 'NOT_RUN' };
      output.dispatch_call_target = 'NOT_SENT';
      output.native_dispatched_target = 'UNKNOWN';
      output.receipt_target_match = 'UNKNOWN';
      output.native_return_type = 'NOT_APPLICABLE';
    }
    syncGroundedDispatch(output, dispatchContext);
    if (!validId || typeof options.invoke !== 'function') {
      output.status = 'INVALID_HELPER_ARGUMENTS';
      output.blockers = [!validId ? 'INVALID_OPERATION_ID' : 'INVOKE_FUNCTION_REQUIRED'];
      return output;
    }

    const paths = await validatePrivatePaths(options.taskDir, options.inputDir);
    if (!paths.ok) {
      output.status = 'PRIVATE_PATHS_INVALID';
      output.blockers = [paths.error && paths.error.code || 'PRIVATE_PATHS_INVALID'];
      return output;
    }
    const base = path.join(paths.observation_dir, options.operationId + '.input');
    output.files = {
      request: base + '.request.json',
      raw_return: base + '.raw.json',
      diagnostic: base + '.diagnostic.json',
    };

    let requestBytes;
    try {
      const requestEnvelope = {
        schema: output.schema,
        operation_id: options.operationId,
        request: options.request,
      };
      const requestGap = jsonSerializationGap(requestEnvelope);
      if (requestGap) throw new TypeError('REQUEST_NOT_JSON_COMPLETE:' + requestGap);
      const requestText = JSON.stringify(requestEnvelope);
      if (typeof requestText !== 'string') throw new TypeError('REQUEST_NOT_JSON_SERIALIZABLE');
      requestBytes = Buffer.from(requestText + '\n', 'utf8');
    } catch (error) {
      output.status = 'REQUEST_SERIALIZATION_FAILED';
      output.request = { status: 'SERIALIZATION_FAILED', error: inputErrorSnapshot(error) };
      output.blockers = ['REQUEST_SERIALIZATION_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    output.request = {
      status: 'PREPARED',
      bytes: requestBytes.length,
      sha256: sha256(requestBytes),
      write: 'NOT_RUN',
      readback: 'NOT_RUN',
    };
    const requestWrite = await writeExclusive(output.files.request, requestBytes);
    output.request.write = requestWrite.status;
    if (requestWrite.error) output.request.write_error = inputErrorSnapshot(requestWrite.error);
    if (requestWrite.status !== 'WRITTEN') {
      output.status = 'REQUEST_PERSIST_FAILED';
      output.blockers = ['REQUEST_PERSIST_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    const requestReadback = await (options.readbackExact || readbackExact)(
      output.files.request, requestBytes);
    output.request.readback = requestReadback.status;
    output.request.saved_bytes = requestReadback.saved_bytes;
    output.request.saved_sha256 = requestReadback.saved_sha256;
    if (requestReadback.error) output.request.readback_error = inputErrorSnapshot(requestReadback.error);
    if (requestReadback.status !== 'MATCH') {
      output.status = 'REQUEST_READBACK_FAILED';
      output.blockers = ['REQUEST_READBACK_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    let returned;
    let rawEnvelope;
    output.status = 'INVOKED';
    try {
      // Invoke from the bytes that were written and read back. Never pass the
      // caller's mutable object across the persistence boundary.
      const savedEnvelope = JSON.parse(requestBytes.toString('utf8'));
      returned = await options.invoke(savedEnvelope.request);
      output.raw_return.kind = 'RETURN';
      if (returned === undefined) {
        output.raw_return.kind = 'NATIVE_RETURN_UNDEFINED';
        output.raw_return.value_type = 'undefined';
        rawEnvelope = { kind: 'NATIVE_RETURN_UNDEFINED', value_type: 'undefined' };
      } else {
        output.raw_return.value_type = 'VALUE';
        rawEnvelope = { kind: 'RETURN', value: returned };
      }
    } catch (error) {
      const snapshot = inputErrorSnapshot(error);
      output.raw_return.kind = 'ERROR';
      output.raw_return.error_summary = inputErrorSummary(snapshot);
      rawEnvelope = { kind: 'ERROR', error: snapshot };
    }

    let rawBytes;
    try {
      const rawGap = jsonSerializationGap(rawEnvelope);
      if (rawGap) throw new TypeError('RAW_NOT_JSON_COMPLETE:' + rawGap);
      const rawText = JSON.stringify(rawEnvelope);
      if (typeof rawText !== 'string') throw new TypeError('RETURN_NOT_JSON_SERIALIZABLE');
      rawBytes = Buffer.from(rawText + '\n', 'utf8');
    } catch (error) {
      output.status = 'RAW_SERIALIZATION_FAILED';
      output.raw_return.status = 'SERIALIZATION_FAILED';
      output.raw_return.complete = false;
      output.raw_return.gap = '原始回傳含循環或不可 JSON 序列化欄位；未保存為完整 raw。';
      output.raw_return.serialization_error = inputErrorSummary(inputErrorSnapshot(error));
      output.blockers = ['RAW_SERIALIZATION_FAILED'];
      await persistInputDiagnostic(output, options, dispatchContext);
      return output;
    }

    output.raw_return.bytes = rawBytes.length;
    output.raw_return.sha256 = sha256(rawBytes);
    output.raw_return.write = 'NOT_RUN';
    output.raw_return.readback = 'NOT_RUN';
    const rawWrite = await writeExclusive(output.files.raw_return, rawBytes);
    output.raw_return.write = rawWrite.status;
    if (rawWrite.error) output.raw_return.write_error = inputErrorSnapshot(rawWrite.error);
    if (rawWrite.status === 'WRITTEN') {
      const rawReadback = await (options.readbackExact || readbackExact)(
        output.files.raw_return, rawBytes);
      output.raw_return.readback = rawReadback.status;
      output.raw_return.saved_bytes = rawReadback.saved_bytes;
      output.raw_return.saved_sha256 = rawReadback.saved_sha256;
      if (rawReadback.error) output.raw_return.readback_error = inputErrorSnapshot(rawReadback.error);
      output.raw_return.status = rawReadback.status;
      output.raw_return.complete = rawReadback.status === 'MATCH' &&
        (output.raw_return.kind !== 'ERROR' ||
         output.raw_return.error_summary.fields_complete);
      if (!output.raw_return.complete) {
        output.raw_return.gap = '原始回傳寫入／讀回不完整；不得視為完整 raw。';
      }
    } else {
      output.raw_return.status = 'WRITE_FAILED';
      output.raw_return.complete = false;
    }
    if (!output.raw_return.complete) output.blockers = ['RAW_RETURN_INCOMPLETE'];
    await persistInputDiagnostic(output, options, dispatchContext);
    return output;
  }

  function groundedDownloadOutput(operationId) {
    return {
      schema: 'line-notes-grounded-download-click/v1',
      operation_id: typeof operationId === 'string' && operationId
        ? operationId : 'UNKNOWN',
      status: 'NOT_INVOKED',
      blockers: [],
      request: { status: 'NOT_RUN' },
      raw_return: { status: 'NOT_RUN', complete: false },
      diagnostic: { status: 'NOT_RUN', complete: false },
      files: {},
      source_observation_readback: { status: 'NOT_RUN' },
      mapping_evidence_readback: { status: 'NOT_RUN' },
      dispatch_call_target: 'NOT_SENT',
      native_dispatched_target: 'UNKNOWN',
      receipt_target_match: 'UNKNOWN',
      receipt_is_os_event_trace: false,
      native_return_type: 'NOT_APPLICABLE',
      hostCalls: normalizeHostCalls(null, [
        'dispatch_call_started_at', 'dispatch_call_returned_at',
      ]),
    };
  }

  function isPlainObject(value) {
    if (value === null || typeof value !== 'object' || Array.isArray(value)) {
      return false;
    }
    try {
      const prototype = Object.getPrototypeOf(value);
      return prototype === Object.prototype || prototype === null;
    } catch (error) {
      return false;
    }
  }

  function isKnownString(value) {
    return typeof value === 'string' && value.length > 0 && value !== 'UNKNOWN';
  }

  function isKnownIdentifier(value) {
    return isKnownString(value) ||
      (Number.isSafeInteger(value) && value >= 0);
  }

  function isFileRef(value) {
    return isPlainObject(value) && isKnownString(value.path) &&
      Number.isSafeInteger(value.bytes) && value.bytes > 0 &&
      typeof value.sha256 === 'string' && /^[0-9a-f]{64}$/.test(value.sha256);
  }

  function sameFileRef(left, right) {
    return isFileRef(left) && isFileRef(right) &&
      left.path === right.path && left.bytes === right.bytes &&
      left.sha256 === right.sha256;
  }

  function groundedWindowBlockers(window) {
    return isPlainObject(window) &&
      window.app_bundle_id === 'jp.naver.line.mac' &&
      isKnownIdentifier(window.window_id)
      ? [] : ['APP_WINDOW_CONTEXT_REQUIRED'];
  }

  function groundedCoordinateBlockers(request, prefix = 'DOWNLOAD_CONTROL',
                                       options = {}) {
    const blockers = [];
    const add = (name, invalid) => {
      if (invalid) blockers.push(prefix + '_' + name);
    };
    add('MAPPING_UNKNOWN', request.mapping_status !== 'MATCH');
    add('OBSERVATION_ORDER_UNKNOWN', request.observation_order !== 'PRE_INPUT');
    add('GROUNDING_NOT_PASS', options.requireGrounding !== false &&
        request.grounding_conclusion !== 'PASS_TO_INPUT');
    add('POINT_RELATION_INVALID', options.requirePointRelation !== false &&
        request.candidate_point_relation !== 'INSIDE');
    add('COORDINATE_SPACE_UNKNOWN', request.coordinate_space_match !== 'MATCH');
    add('TARGET_COORD_SPACE_INVALID',
      !isKnownString(request.control_region_coord_space) ||
      !isKnownString(request.target_coord_space) ||
      request.control_region_coord_space !== request.target_coord_space);
    return blockers;
  }

  function groundedGeometryBlockers(region, point, target, labels = {}) {
    const finitePoint = value => Array.isArray(value) && value.length === 2 &&
      value.every(Number.isFinite);
    const validRegion = Array.isArray(region) && region.length === 4 &&
      region.every(Number.isFinite) && region[2] > region[0] &&
      region[3] > region[1];
    if (!validRegion || !finitePoint(point) || !finitePoint(target)) {
      return [labels.missing || 'DOWNLOAD_CONTROL_GEOMETRY_MISSING_OR_NONFINITE'];
    }
    const blockers = [];
    const strictInterior = point[0] > region[0] && point[0] < region[2] &&
      point[1] > region[1] && point[1] < region[3];
    if (!strictInterior) blockers.push(labels.interior ||
      'DOWNLOAD_CONTROL_POINT_NOT_STRICT_INTERIOR');
    if (labels.targetMismatch !== null &&
        (point[0] !== target[0] || point[1] !== target[1])) {
      blockers.push(labels.targetMismatch ||
        'DOWNLOAD_CONTROL_PREPARED_TARGET_MISMATCH');
    }
    return blockers;
  }

  function groundedRequestBlockers(request) {
    const blockers = [];
    const add = code => { if (!blockers.includes(code)) blockers.push(code); };
    if (!isPlainObject(request)) return ['DOWNLOAD_CONTROL_REQUEST_INVALID'];
    const source = request.source_observation;
    if (request.input_phase !== 'DOWNLOAD_CONTROL') {
      add('DOWNLOAD_CONTROL_PHASE_REQUIRED');
    }
    if (!isKnownString(request.attempt_id)) add('ATTEMPT_ID_REQUIRED');
    blockers.push(...groundedWindowBlockers(request.app_window_binding));
    blockers.push(...groundedCoordinateBlockers(request));
    if (!isFileRef(source) ||
        !sameFileRef(source, request.source_observation_ref)) {
      add('DOWNLOAD_CONTROL_SOURCE_REF_MISMATCH');
    }
    if (!isFileRef(request.mapping_evidence_ref)) {
      add('DOWNLOAD_CONTROL_MAPPING_REF_INVALID');
    }
    blockers.push(...groundedGeometryBlockers(
      request.control_region, request.candidate_point, request.prepared_target));
    return blockers;
  }

  async function privateFileReadback(fileRef, taskDir, copied, role) {
    const result = { status: 'NOT_RUN', role };
    const prefix = role === 'MAPPING_EVIDENCE'
      ? 'MAPPING_EVIDENCE' : 'SOURCE_OBSERVATION';
    if (!isFileRef(fileRef)) {
      result.status = 'FAILED';
      result.blocker = prefix + '_REF_REQUIRED';
      return result;
    }
    if (copied) {
      if (!copied.ok) {
        result.status = 'FAILED';
        result.blocker = 'SOURCE_OBSERVATION_BYTES_REQUIRED';
        return result;
      }
      result.expected_bytes = copied.bytes.length;
      result.expected_sha256 = sha256(copied.bytes);
      if (fileRef.bytes !== result.expected_bytes ||
          fileRef.sha256 !== result.expected_sha256) {
        result.status = 'MISMATCH';
        result.blocker = prefix + '_REF_BYTES_MISMATCH';
        return result;
      }
    } else {
      result.expected_bytes = fileRef.bytes;
      result.expected_sha256 = fileRef.sha256;
    }
    result.path = fileRef.path;
    try {
      if (!path.isAbsolute(fileRef.path)) throw new Error('ABSOLUTE_PATH_REQUIRED');
      const taskReal = await fs.realpath(taskDir);
      const real = await fs.realpath(fileRef.path);
      if (path.resolve(fileRef.path) !== real) {
        throw new Error('CANONICAL_SOURCE_REQUIRED');
      }
      if (real !== taskReal && !real.startsWith(taskReal + path.sep)) {
        throw new Error('SOURCE_OUTSIDE_TASK');
      }
      const info = await fs.lstat(real);
      if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1) {
        throw new Error('REGULAR_SINGLE_LINK_SOURCE_REQUIRED');
      }
      const saved = await fs.readFile(real);
      result.saved_bytes = saved.length;
      result.saved_sha256 = sha256(saved);
      result.status = saved.length === result.expected_bytes &&
        result.saved_sha256 === result.expected_sha256 ? 'MATCH' : 'MISMATCH';
      if (result.status !== 'MATCH') {
        result.blocker = prefix + '_READBACK_MISMATCH';
      }
      return result;
    } catch (error) {
      result.status = 'FAILED';
      result.blocker = prefix + '_READBACK_FAILED';
      result.error = describeError(error);
      return result;
    }
  }

  async function persistGroundedDownloadClick(options) {
    const output = groundedDownloadOutput(options && options.operationId);
    const operationId = output.operation_id;
    if (!options || typeof options !== 'object') {
      output.status = 'INVALID_HELPER_ARGUMENTS';
      output.blockers = ['OPTIONS_REQUIRED'];
      return output;
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(operationId)) {
      output.status = 'INVALID_HELPER_ARGUMENTS';
      output.blockers = ['INVALID_OPERATION_ID'];
      return output;
    }

    // Snapshot the caller's request and source bytes before the first await.
    // Later path and file reads must never observe mutations to these objects.
    const requestSnapshot = snapshotJsonValue(options.request);
    const sourceCopy = copyExactUint8Array(options.source_observation_bytes);
    const app = options.app;
    const click = app && typeof app.click === 'function'
      ? app.click.bind(app) : null;
    const requestBlockers = requestSnapshot.ok
      ? groundedRequestBlockers(requestSnapshot.value) : [];
    const paths = await validatePrivatePaths(options.taskDir, options.inputDir);
    if (!paths.ok) {
      output.status = 'PRIVATE_PATHS_INVALID';
      output.blockers = [paths.error && paths.error.code || 'PRIVATE_PATHS_INVALID'];
      return output;
    }
    output.files.diagnostic = path.join(
      paths.observation_dir, operationId + '.input.diagnostic.json');
    if (!requestSnapshot.ok) {
      output.status = 'REQUEST_SERIALIZATION_FAILED';
      output.request = {
        status: 'SERIALIZATION_FAILED',
        error: requestSnapshot.error || {
          name: 'TypeError',
          message: requestSnapshot.code + (requestSnapshot.detail
            ? ':' + requestSnapshot.detail : ''),
        },
      };
      output.blockers = ['REQUEST_SERIALIZATION_FAILED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    const request = requestSnapshot.value;
    if (requestBlockers.length > 0) {
      output.status = 'DOWNLOAD_CONTROL_GROUNDING_INVALID';
      output.blockers = requestBlockers;
      await persistInputDiagnostic(output, {});
      return output;
    }
    if (!sourceCopy.ok) {
      output.status = 'SOURCE_OBSERVATION_BYTES_REQUIRED';
      output.blockers = ['SOURCE_OBSERVATION_BYTES_REQUIRED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    const sourceReadback = await privateFileReadback(
      request.source_observation, paths.task_dir, sourceCopy,
      'SOURCE_OBSERVATION');
    output.source_observation_readback = sourceReadback;
    if (sourceReadback.status !== 'MATCH') {
      output.status = 'SOURCE_OBSERVATION_READBACK_FAILED';
      output.blockers = [sourceReadback.blocker || 'SOURCE_OBSERVATION_READBACK_FAILED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    const mappingReadback = await privateFileReadback(
      request.mapping_evidence_ref, paths.task_dir, null,
      'MAPPING_EVIDENCE');
    output.mapping_evidence_readback = mappingReadback;
    if (mappingReadback.status !== 'MATCH') {
      output.status = 'MAPPING_EVIDENCE_READBACK_FAILED';
      output.blockers = [mappingReadback.blocker || 'MAPPING_EVIDENCE_READBACK_FAILED'];
      await persistInputDiagnostic(output, {});
      return output;
    }
    if (click === null) {
      output.status = 'APP_CLICK_UNAVAILABLE';
      output.blockers = ['APP_CLICK_UNAVAILABLE'];
      await persistInputDiagnostic(output, {});
      return output;
    }

    const hostCalls = {
      dispatch_call_started_at: 'NOT_RUN',
      dispatch_call_returned_at: 'NOT_RUN',
    };
    const dispatch = {
      call_target: 'NOT_SENT',
      return_type: 'NOT_APPLICABLE',
    };
    const result = await persistSingleInputInternal({
      taskDir: paths.task_dir,
      inputDir: paths.observation_dir,
      operationId,
      request,
      invoke: async saved => {
        const savedPoint = saved.prepared_target;
        const target = [savedPoint[0], savedPoint[1]];
        dispatch.call_target = target;
        try {
          hostCalls.dispatch_call_started_at = new Date().toISOString();
          const returned = await click(target);
          dispatch.return_type = returned === undefined ? 'UNDEFINED' : 'VALUE';
          return returned;
        } catch (error) {
          dispatch.return_type = 'ERROR';
          throw error;
        } finally {
          hostCalls.dispatch_call_returned_at = new Date().toISOString();
        }
      },
    }, {
      token: groundedDispatchToken,
      dispatch,
      hostCalls,
      sourceObservationReadback: sourceReadback,
      mappingEvidenceReadback: mappingReadback,
    });
    return result;
  }

  async function persistInputDiagnostic(output, options, dispatchContext = null) {
    if (!output.files.diagnostic) return;
    if (dispatchContext) syncGroundedDispatch(output, dispatchContext);
    const diagnostic = {
      schema: 'line-notes-single-input-diagnostic/v1',
      operation_id: output.operation_id,
      request: output.request,
      raw_return: output.raw_return,
      status: output.status,
      blockers: output.blockers || [],
      receipt_is_os_event_trace: false,
    };
    for (const key of [
      'source_observation_readback',
      'mapping_evidence_readback',
      'dispatch_call_target',
      'native_dispatched_target',
      'receipt_target_match',
      'native_return_type',
      'hostCalls',
    ]) {
      if (Object.prototype.hasOwnProperty.call(output, key)) {
        diagnostic[key] = output[key];
      }
    }
    let bytes;
    try {
      bytes = Buffer.from(JSON.stringify(diagnostic, null, 2) + '\n', 'utf8');
    } catch (error) {
      output.diagnostic = { status: 'SERIALIZATION_FAILED', complete: false,
                            error: inputErrorSnapshot(error) };
      output.blockers = [...(output.blockers || []), 'DIAGNOSTIC_PERSISTENCE_INCOMPLETE'];
      return;
    }
    const written = await writeExclusive(output.files.diagnostic, bytes);
    output.diagnostic = {
      status: written.status,
      complete: false,
      bytes: bytes.length,
      sha256: sha256(bytes),
      readback: 'NOT_RUN',
    };
    if (written.error) output.diagnostic.write_error = inputErrorSnapshot(written.error);
    if (written.status !== 'WRITTEN') {
      output.blockers = [...(output.blockers || []), 'DIAGNOSTIC_PERSISTENCE_INCOMPLETE'];
      return;
    }
    const readback = await (options.readbackExact || readbackExact)(
      output.files.diagnostic, bytes);
    output.diagnostic.readback = readback.status;
    output.diagnostic.saved_bytes = readback.saved_bytes;
    output.diagnostic.saved_sha256 = readback.saved_sha256;
    output.diagnostic.complete = readback.status === 'MATCH';
    if (readback.error) output.diagnostic.readback_error = inputErrorSnapshot(readback.error);
    if (!output.diagnostic.complete) {
      output.blockers = [...(output.blockers || []), 'DIAGNOSTIC_PERSISTENCE_INCOMPLETE'];
    }
  }

  async function captureAndPersist(options) {
    let capture = null;
    let captureError = null;
    const hostCalls = {
      capture_call_started_at: 'NOT_RUN',
      capture_call_returned_at: 'NOT_RUN',
    };
    try {
      const app = await cua.getApp('jp.naver.line.mac');
      hostCalls.capture_call_started_at = new Date().toISOString();
      try {
        capture = await app.getAXStateAndScreenshot({
          disableDiffing: true,
          emit: false,
        });
      } finally {
        hostCalls.capture_call_returned_at = new Date().toISOString();
      }
    } catch (error) {
      captureError = describeError(error);
    }
    return persistObservation(
      Object.assign({}, options, { capture, captureError, hostCalls }));
  }

  return {
    captureAndPersist,
    copyExactUint8Array,
    describeError,
    groundedCoordinateBlockers,
    groundedGeometryBlockers,
    groundedWindowBlockers,
    persistObservation,
    persistGroundedDownloadClick,
    persistSingleInput,
    readbackExact,
    sha256,
    snapshotJsonValue,
    writeExclusive,
  };
}
