import asyncio
import html
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import aiohttp
from aiohttp import ClientTimeout

from config import SCHEDULE_API_BASE_URL

SUBJECT_TYPES = {
    "Lecture": "Лекция",
    "Seminar": "Семинар",
    "Laboratory": "Лабораторная",
}


def _merge_parallel_lessons(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Одно занятие на несколько групп (общая лекция и т.п.) — один блок,
    список групп через запятую. Ключ совпадения: время, название, тип,
    подгруппа, аудитория.
    """
    merged_order: List[tuple] = []
    template: Dict[tuple, Dict[str, Any]] = {}
    groups_by_key: Dict[tuple, List[str]] = {}

    for subj in lessons:
        sg = subj.get("subgroup", "Common")
        room = str(subj.get("classroom") or "").strip()
        key = (
            subj["time"]["start"],
            subj["time"]["end"],
            str(subj.get("title") or "").strip(),
            str(subj.get("type") or "").strip(),
            sg,
            room,
        )
        if key not in template:
            template[key] = dict(subj)
            groups_by_key[key] = []
            merged_order.append(key)
        g = subj.get("group")
        if g and g not in groups_by_key[key]:
            groups_by_key[key].append(g)

    out: List[Dict[str, Any]] = []
    for key in merged_order:
        row = dict(template[key])
        groups = groups_by_key[key]
        if groups:
            row["group"] = ", ".join(sorted(groups))
        out.append(row)

    out.sort(key=lambda x: x["time"]["start"])
    return out


def sanitize_professor_slug(name: str) -> str:
    """Так же, как sanitize_professor_filename в multitool_api (имя файла без .json)."""
    s = name.strip()
    for c in '<>:"/\\|?*':
        s = s.replace(c, "_")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def format_professor_schedule_day(
    lessons: List[Dict[str, Any]],
    day: int,
    month: int,
    professor_display: str,
) -> str:
    safe_prof = html.escape(professor_display)
    formatted_date = f"{day:02d}.{month:02d}"

    if not lessons:
        return (
            f"📅 На <b>{formatted_date}</b> у преподавателя "
            f"<b>{safe_prof}</b> занятий нет."
        )

    lessons = _merge_parallel_lessons(lessons)

    lines = []
    for subj in lessons:
        title = html.escape(str(subj.get("title") or "—"))
        subject_type = html.escape(
            str(SUBJECT_TYPES.get(subj.get("type"), subj.get("type") or "—"))
        )
        classroom = html.escape(str(subj.get("classroom") or "Не указана"))
        time_start = subj["time"]["start"]
        time_end = subj["time"]["end"]
        group_raw = str(subj.get("group") or "—")
        group = html.escape(group_raw)
        group_parts = [p.strip() for p in group_raw.split(",") if p.strip()]
        group_label = "группы" if len(group_parts) > 1 else "группа"

        sg_raw = subj.get("subgroup", "Common")
        subj_subgroup_translated = {"A": "А", "B": "Б"}.get(sg_raw, sg_raw)
        subgroup_info = (
            f", подгруппа {subj_subgroup_translated}" if sg_raw != "Common" else ""
        )

        lines.append(
            f"⏰ <b>{time_start} — {time_end}</b>{subgroup_info}\n"
            f" {title} ({subject_type})\n"
            f" {group_label} <b>{group}</b>, ауд. {classroom}\n"
        )

    return (
        f"📅 Расписание преподавателя <b>{safe_prof}</b> на <b>{formatted_date}</b>:\n\n"
        + "\n".join(lines)
    )


async def fetch_professor_schedule_for_day(
    professor_slug: str,
    day: int,
    month: int,
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    GET /schedule/professor/{slug}?day=&month=
    Возвращает (сообщение_об_ошибке_или_None, список_занятий).
    При успехе ошибка None; список может быть пустым.
    """
    base = SCHEDULE_API_BASE_URL.rstrip("/")
    path_segment = quote(professor_slug, safe="")
    url = f"{base}/schedule/professor/{path_segment}"

    timeout = ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url,
                params={"day": day, "month": month},
            ) as resp:
                text_body = await resp.text()
                if resp.status == 404:
                    return "not_found", []
                if resp.status != 200:
                    return "http_error", []
                try:
                    data = json.loads(text_body)
                except json.JSONDecodeError:
                    return "bad_json", []
                lessons = data.get("lessons")
                if not isinstance(lessons, list):
                    return "bad_json", []
                return None, lessons
    except aiohttp.ClientError:
        return "connection", []
    except asyncio.TimeoutError:
        return "timeout", []
