from dataclasses import dataclass


@dataclass
class StudyInfo:
    experimenter: list[str]
    experiment_description: str
    lab: str
    institution: str