import tempfile
from nexus_ig.core.storage import Storage
from nexus_ig.core.bot import NexusBot


def test_storage_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test_nexus.db"
        store = Storage(db_path)
        assert store.has_greeted("12345") is False
        store.mark_greeted("12345", "Test Group")
        assert store.has_greeted("12345") is True
        store.close()



def test_nexus_bot_class():
    bot = NexusBot()
    assert bot.config is not None

