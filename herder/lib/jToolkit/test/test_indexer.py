from jToolkit.data import indexer
import os

def clear_directory(directory):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                clear_directory(filepath)
            else:
                os.remove(filepath)
        os.rmdir(directory)

class TestIndexer:
    """tests the standard Indexer"""
    def setup_method(self, method):
        self.indexdir = "%s.index" % method.__name__
        clear_directory(self.indexdir)
        self.indexer = indexer.Indexer(self)
        self.searcher = indexer.Searcher(self.indexdir)

    def teardown_method(self, method):
        self.searcher.close()
        clear_directory(self.indexdir)

    def test_create_index(self):
        self.indexer.startIndex()
        self.indexer.commitIndex()

    def test_delete_index(self):
        assert self.indexer.deleteIndex() == True

    def test_add_records(self):
        self.indexer.startIndex()
        records = [{"species": "bunny", "name": "Benjamin"}, {"species": "leopard", "name": "Standard"}, {"species": "complex creature", "names": "Bob Ann"}]
        self.indexer.indexFields(records)
        self.indexer.commitIndex()
        assert self.searcher.searchField("species", "bunny", "name") == [{"name": "Benjamin"}]
        assert self.searcher.searchField("name", "Standard", "species") == [{"species": "leopard"}]

    def test_search_all(self):
        self.test_add_records()
        assert self.searcher.searchAllFields("bunny",["name"]) == [{'name':'Benjamin'}]
        assert self.searcher.searchAllFields("bunny",(["name"],["species"])) == [{'name':'Benjamin'}]
        assert self.searcher.searchAllFields("complex",(["name"],["names"])) == [{'names':'Bob Ann'}]

    def test_delete_records(self):
        self.test_add_records()
        assert self.searcher.deleteDoc({"species": "bunny"}) == 1
        assert self.searcher.searchField("species", "bunny", "name") == []
        assert self.searcher.searchField("name", "Standard", "species") == [{"species": "leopard"}]

class TestIndexerProcess(TestIndexer):
    """tests the Indexer proxying through to another Indexer"""
    def setup_class(self):
        indexer.OldIndexer = indexer.Indexer
        indexer.OldSearcher = indexer.Searcher
        indexer.LaunchIndexProcess()
	indexer.INSIDE_APACHE = True

    def teardown_class(self):
        indexer.Indexer = indexer.OldIndexer
        indexer.Searcher = indexer.OldSearcher

