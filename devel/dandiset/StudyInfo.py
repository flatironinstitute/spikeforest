from dataclasses import dataclass
from pynwb.file import Subject


@dataclass
class StudyInfo:
    experimenter: "list[str]"
    experiment_description: str
    lab: str
    institution: str
    keywords: "list[str]"
    subject: Subject