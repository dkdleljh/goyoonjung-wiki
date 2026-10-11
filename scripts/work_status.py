"""Conservative interpretation of explicit work status, never inferred from year/platform."""

import re


def work_status(note: str) -> str:
    if re.search(r"비공식|루머|검토|미확정|미공개|미정|불발|취소|확인 필요", note):
        return "unknown"
    if re.search(r"예정|예고|pending release|공개 계획|방영 계획", note, re.I):
        return "reported_once"
    if re.search(r"공개됨|공개 완료|방영됨|방영 완료|종영|개봉됨|개봉 완료", note):
        return "released"
    return "unknown"


def is_future_candidate(line: str) -> bool:
    # Editorial tasks and retrospective interviews are not work announcements.
    if re.search(r"보강|작성|추가|정리|업데이트|촬영 당시|인터뷰", line):
        return False
    return bool(re.search(r"공개 예정|방영 예정|개봉 예정|출연 검토|캐스팅|제작 예정|pending release", line, re.I))
