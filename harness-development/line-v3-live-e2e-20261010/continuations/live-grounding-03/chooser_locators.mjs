const fail = code => { throw Object.assign(new Error(code), {code}); };
const need = (value, code) => { if (!value) fail(code); };
const HEX64 = /^[0-9a-f]{64}$/;

function phase(envelope, expected) {
  need(envelope?.version === 1 && envelope.phase === expected && envelope.frame?.frame_id
    && HEX64.test(envelope.frame.frame_id), 'CHOOSER_PHASE_REQUIRED');
  return envelope;
}

export function createChooserLocators() {
  return Object.freeze({
    locatePathField(envelope) {
      phase(envelope, 'GO_TO_FOLDER');
      const control = envelope.control;
      need(Number.isInteger(control?.path_field_index) && control.path_field_index >= 0
        && control.path_field_role === 'text field' && control.path_field_subrole === 'PathTextField'
        && control.path_field_enabled === true && control.focused === true, 'PATH_FIELD_UNKNOWN');
      return Object.freeze({index:control.path_field_index,frameId:envelope.frame.frame_id,
        role:control.path_field_role,subrole:control.path_field_subrole,
        enabled:control.path_field_enabled,identifier:control.path_field_identifier,bounds_px:[...control.path_field_bounds_px]});
    },
    validatePath(envelope, expectedPath) {
      phase(envelope, 'PATH_FILLED');
      const control = envelope.control;
      return typeof expectedPath === 'string' && control.value === expectedPath
        && control.path_field_role === 'text field' && control.path_field_subrole === 'PathTextField'
        && control.path_field_enabled === true && control.focused === true;
    },
    validateLeaf(envelope, expectedPath) {
      phase(envelope, 'DESTINATION_SELECTED');
      const control = envelope.control;
      const leaf = expectedPath.split('/').at(-1);
      return control.value === expectedPath && control.selected_leaf === leaf
        && Number.isInteger(control.selected_leaf_index) && typeof control.selected_leaf_identifier==='string'
        && Array.isArray(control.selected_leaf_bounds_px) && control.selected_leaf_ocr?.text===leaf
        && Array.isArray(control.selected_leaf_ocr?.bounds)
        && control.path_field_enabled === true
        && control.path_field_role === 'text field' && control.path_field_subrole === 'PathTextField'
        && control.confirm_role === 'button' && control.confirm_enabled === true;
    },
    locateConfirm(envelope) {
      phase(envelope, 'DESTINATION_SELECTED');
      const control = envelope.control;
      need(control.confirm_role === 'button' && control.confirm_enabled === true, 'CONFIRM_CONTROL_UNKNOWN');
      const bounds = control.confirm_bounds_px;
      const point = [Math.trunc(bounds[0] + bounds[2] / 2), Math.trunc(bounds[1] + bounds[3] / 2)];
      need(point.every(Number.isInteger), 'CONFIRM_CONTROL_UNKNOWN');
      return Object.freeze({point,frameId:envelope.frame.frame_id,role:control.confirm_role,enabled:control.confirm_enabled,
        elementIndex:control.confirm_index,identifier:control.confirm_identifier,bounds_px:[...bounds]});
    },
  });
}
