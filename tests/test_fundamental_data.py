import unittest
from fundamental_data import normalize_finnhub,series_rows,CONTRACTS

class FundamentalTests(unittest.TestCase):
    def approved(self,field):
        spec=CONTRACTS[field]
        return {field:{'unit':spec.unit,'period':spec.period,'definition':'Contrato simulado para prueba','reference':'test fixture, no validación real'}}
    def row(self,field,value,**kwargs):
        return next(row for row in normalize_finnhub({field:value},'2026-10-13',**kwargs) if row['field']==field)
    def test_percentage_points_fraction(self):
        for field in ('roeTTM','roaTTM','grossMarginTTM','operatingMarginTTM','netProfitMarginTTM','currentDividendYieldTTM','payoutRatioAnnual'):
            for value in (25.,-.5,0.,150.):
                result=self.row(field,value,approvals=self.approved(field))
                self.assertEqual(result['normalized_value'],value/100)
                self.assertEqual(result['raw_value'],value)
                self.assertFalse(result['valuation_ready'])
    def test_no_unapproved_conversions(self):
        self.assertIsNone(self.row('roeTTM',.25)['normalized_value'])
        self.assertEqual(self.row('roeTTM',.25)['status'],'pending_contract')
        wrong=self.approved('roeTTM');wrong['roeTTM']['unit']='ratio'
        self.assertIsNone(self.row('roeTTM',25,approvals=wrong)['normalized_value'])
    def test_ratios_eps_periods(self):
        for field in ('peTTM','forwardPE','pegTTM'):
            self.assertEqual(self.row(field,25,approvals=self.approved(field))['normalized_value'],25)
        self.assertIsNone(self.row('epsTTM',4,approvals=self.approved('epsTTM'))['normalized_value'])
        result=self.row('epsTTM',4,approvals=self.approved('epsTTM'),currency='USD')
        self.assertEqual(result['normalized_value'],4)
        self.assertEqual(result['currency'],'USD')
        self.assertEqual(self.row('epsAnnual',4)['period_kind'],'annual')
        self.assertEqual(self.row('forwardPE',4)['period_kind'],'forward')
    def test_missing_invalid_zero(self):
        for value in (None,True,False,'3',float('inf'),float('nan')):
            self.assertIsNone(self.row('peTTM',value)['normalized_value'])
            self.assertEqual(self.row('peTTM',value)['status'],'invalid_or_empty')
        self.assertEqual(self.row('peTTM',0,approvals=self.approved('peTTM'))['normalized_value'],0)
        rows=normalize_finnhub({},'today')
        self.assertTrue(all(row['status']=='missing' for row in rows))
    def test_dates_not_invented_and_sources_separate(self):
        data={'roeTTM':25,'__series__':{'annual':{'roe':[{'period':'2025-06-30','v':25},{'period':'bad','v':20}]}}}
        original=str(data)
        rows=normalize_finnhub(data,'2026-10-13',stale=True)
        self.assertTrue(all(row['economic_date'] is None for row in rows))
        series=series_rows(data,'2026-10-13',True)
        self.assertEqual(len(series),1)
        self.assertEqual(series[0]['economic_date'],'2025-06-30')
        self.assertEqual(series[0]['fetched_at'],'2026-10-13')
        self.assertEqual(str(data),original)
        self.assertTrue(all(row['source']=='Finnhub' for row in rows))

    def test_series_transport_preserves_dates_not_secrets(self):
        from unittest.mock import Mock,patch
        from finnhub_provider import transport
        import json
        response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.read.return_value=json.dumps({'metric':{'roeTTM':20},'series':{
            'annual':{'roe':[{'period':'2025-06-30','v':20},{'period':'invalid','v':1},{'period':'2025-06-30','v':True}]},
            'quarterly':{'eps':[{'period':'2025-09-30','v':2}]}}}).encode()
        with patch('finnhub_provider.urlopen',return_value=response):
            data=transport('TEST_SECRET','MSFT','metrics')
        self.assertEqual(data['roeTTM'],20)
        rows=series_rows(data,'2026-10-13')
        self.assertEqual(len(rows),2)
        self.assertEqual({row['period_kind'] for row in rows},{'annual','quarterly'})
        self.assertTrue(all(row['economic_date'] != row['fetched_at'] for row in rows))
        self.assertNotIn('TEST_SECRET',str(data))
