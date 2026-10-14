import os
import sys
import unittest
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,Provider,identity
from line_backup_batch.coordinator import Coordinator
from line_backup_acceptance.common import AcceptanceError


class BatchLifecycleTests(unittest.TestCase):
    def setUp(self):self.f=Fixture(cap=1)
    def tearDown(self):self.f.close()

    def run_batch(self,targets):
        provider=Provider(self.f,targets)
        coordinator=Coordinator(self.f.svc,provider,self.f.binding['binary_path'],self.f.binding['binary_sha256'])
        return coordinator.run(1),provider

    def test_second_cap_one_lifecycle_starts_only_after_release(self):
        first,second=identity(2,1),identity(3,2)
        first_result,first_provider=self.run_batch([first])
        self.assertEqual(first_result['status'],'ALL_COMPLETE')
        self.assertEqual(first_provider.opens,[first])
        self.assertEqual(len(first_provider.dispatches),1)
        state=self.f.state()
        self.assertEqual(state['active_batch']['phase'],'COMPLETED')
        self.assertEqual(state['active_batch']['new_transactions_reserved'],1)
        self.assertIsNone(state['active_writer_id'])

        with self.assertRaisesRegex(AcceptanceError,'BATCH_BUSY'):
            self.f.svc.begin(self.f.receipt(),'backup_batch',1)
        self.f.svc.release(self.f.receipt())
        self.assertIsNone(self.f.state()['active_batch'])

        second_result,second_provider=self.run_batch([first,second])
        self.assertEqual(second_result['status'],'ALL_COMPLETE')
        self.assertEqual(second_provider.opens,[second])
        self.assertEqual(len(second_provider.dispatches),1)
        self.assertEqual(len(second_provider.confirms),1)
        final=self.f.state()
        self.assertEqual(final['active_batch']['phase'],'COMPLETED')
        self.assertEqual(final['active_batch']['new_transactions_reserved'],1)
        self.assertEqual(final['runs'][0]['fingerprint'],first)
        self.assertEqual(final['runs'][1]['fingerprint'],second)
        self.assertEqual(final['runs'][1]['batch_id'],final['active_batch']['batch_id'])
        self.assertEqual(final['active_batch']['next_index'],2)

    def test_unresolved_intent_history_refuses_a_new_cap_one_begin(self):
        target=identity()
        admitted=self.f.svc.begin(self.f.receipt(),'backup_batch',1)['receipt']
        admitted=self.f.svc.admit(admitted,self.f.frames([target]),self.f.session)['receipt']
        self.f.svc.prepare(admitted,self.f.observation([target]))
        self.f.intent(target)
        self.f.svc.stop(self.f.receipt(),'fixture unresolved intent')
        # Isolate the begin history barrier after the terminal lease has been
        # represented as released; the SAFE_ABORT intent remains unresolved.
        state=self.f.state();state['active_batch']=None;self.f.save(state)
        with self.assertRaisesRegex(AcceptanceError,'UNRESOLVED_HISTORY'):
            self.f.svc.begin(self.f.receipt(),'backup_batch',1)


if __name__=='__main__':unittest.main()
