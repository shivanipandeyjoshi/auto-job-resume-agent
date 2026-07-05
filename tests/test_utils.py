from utils.config_manager import ConfigManager
from utils.date_utils import today_str
from utils.text_utils import slugify


def test_config_manager_reads_yaml():
    manager = ConfigManager()
    assert manager.get("project.name") == "local-job-resume-agent"


def test_date_utils():
    value = today_str()
    assert len(value) == 8


def test_slugify():
    assert slugify("Senior Python Engineer") == "senior-python-engineer"
