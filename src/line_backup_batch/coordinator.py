"""Same orchestration entry for external fixture I/O; no native input synthesis."""
from line_backup_acceptance.common import AcceptanceError
from .schema import require

class Coordinator:
    def __init__(self,service,provider,decoder,decoder_sha):
        self.service,self.provider=service,provider
        self.decoder,self.decoder_sha=decoder,decoder_sha

    def run(self,authorized_limit):
        svc=self.service;p=self.provider;receipt=svc.store.snapshot()['receipt'];results=[]
        state=svc.store.snapshot()['state']
        if state.get('active_batch') is not None:return svc.resume()
        receipt=svc.begin(receipt,'backup_batch',authorized_limit)['receipt']
        records,session=p.catalog()
        receipt=svc.admit(receipt,records,session)['receipt']
        try:
            while True:
                s=svc.store.snapshot()['state'];b=s['active_batch']
                if b['next_index']>=len(p.identities):break
                observation=p.observe_album()
                try:prepared=svc.prepare(receipt,observation)
                except AcceptanceError as exc:
                    if exc.code=='LIMIT_REACHED':break
                    raise
                receipt=prepared['receipt'];results.append(prepared['result'])
                if prepared['result']['status']=='SKIP_VERIFIED':continue
                p.open_album(prepared['result'])
                detail,cal,menu,closure=p.calibrate()
                receipt=svc.calibrate(receipt,detail,cal,menu,closure)['receipt']
                fresh=p.detail()
                committed=svc.intent(receipt,fresh);receipt=committed['receipt']
                # The real hosted adapter consumes only this original uninterrupted commit.
                evidence,chooser=p.original_atomic_dispatch(committed)
                receipt=svc.dispatch(receipt,evidence,chooser,True)['receipt']
                finished=svc.finalize(receipt,self.decoder,self.decoder_sha,verify_options=p.verification_io())
                receipt=finished['receipt'];results.append(finished['result'])
            final_records,final_session=p.final_catalog()
            finished=svc.finish(receipt,final_records,final_session)
            return dict(status=finished['result']['status'],results=results,receipt=finished['receipt'],live_gui_verified=False)
        except Exception:
            # Do not mask a failure with a second action or a stale cleanup write.
            current=svc.store.snapshot()['receipt']
            svc.stop(current,'COORDINATOR_FAILURE')
            raise
