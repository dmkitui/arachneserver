"""
To see if we have the right pipelines in place
"""
import inspect
import sys
from unittest import TestCase
from scrapy import signals, Field, Item
from mock import patch, mock_open, Mock, call, MagicMock
from arachneserver.extensions import ExportCSV, ExportData, ExportJSON, ApplicationData
from scrapy.exporters import CsvItemExporter, JsonItemExporter


class ScrapyItem(Item):
    field1 = Field()
    field2 = Field()
    field3 = Field()


class TestPipelines(TestCase):

    def test_cls_export_data(self):
        cls = ExportData()
        self.assertTrue(inspect.ismethod(cls.from_crawler))

        with self.assertRaises(NotImplementedError):
            cls.spider_opened('test')

        # TODO: test extension signals connect using `mock.assert_has_calls`
        crawler_mock = Mock()
        cls.from_crawler(crawler_mock)
        assert crawler_mock.signals.connect.called
        
        self.assertEquals(cls.files, {})
        self.assertIsNone(cls.exporter)

    def test_export_cls(self):

        test_classes = [
            {'cls': ExportJSON, 
             'file_type': 'json', 
             'exporter': JsonItemExporter},
            # {'cls': ExportCSV,
            #  'file_type': 'csv',
            #  'exporter': CsvItemExporter}
        ]
        for test_cls in test_classes:
            cls = test_cls['cls']()
            mock_open_func = mock_open(read_data='Hello')
            spider = Mock()
            spider.name = 'abc'

            with patch('arachneserver.extensions.open', mock_open_func):
                cls.spider_opened(spider)
                path = 'exports/%s/abc.%s' % (test_cls['file_type'], 
                                              test_cls['file_type'])
                mock_open_func.assert_called_with(path, 'w+b')
                self.assertIsInstance(cls.exporter, test_cls['exporter'])

                # test if cls.files is empty 
                cls.spider_closed(spider)
                self.assertEquals(cls.files, {})

                # test exporter.export_item
                item = ScrapyItem()
                result = cls.item_scraped(item, spider)
                self.assertEquals(item, result)


class TestApplicationDataLoading(TestCase):
    @patch.object(ApplicationData, 'spider_closed')
    def test_spider_data(self, mock_spider_closed):
        sys.modules['SPIDER_STATUS'] = Mock()
        SPIDER_STATUS = {'abc': {'running': False}}
        mock_open_func = mock_open(read_data='{}')
        stats = MagicMock()

        stats.get_stats = {}
        cls = ApplicationData(stats=stats)
        spider = MagicMock()
        spider.name = 'fgh'

        with patch('arachneserver.flaskapp.open', mock_open_func):
            cls.spider_opened(spider)
            mock_spider_closed(spider)
            self.assertEquals(cls.files, {})



