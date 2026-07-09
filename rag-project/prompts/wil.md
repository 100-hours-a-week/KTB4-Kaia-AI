You synthesize a week of daily learning-journal entries into one weekly summary, in Korean, for the user's own knowledge base. Base every sentence only on the entries below — do not add facts, topics, or conclusions absent from them.

Input — this week's daily entries:
{til_entries}

Each entry starts with "### YYYY-MM-DD — 주제" and may list concepts as "**개념명**" within its body. Use only headers and concept names that literally appear in {til_entries} — never invent a date, topic, or concept.

Write a markdown summary with exactly these sections, in order:

## 이번 주 학습 지도
A table: 날짜 | 주제 | 핵심 개념. One row per entry, in the order entries appear in {til_entries}. 핵심 개념 = that entry's "**개념명**" items, comma-separated. If an entry has no bolded concept names, use its 주제 as the 핵심 개념 value.

## 이번 주 흐름
2-4 sentences, as a narrative (not a list), on how the week's topics connect or build on each other in the order they actually happened.

## 반복적으로 막힌 지점
Look across all entries for a stuck point that recurred more than once, or one clear unresolved thread carried across days. If nothing recurred, write exactly "이번 주는 반복적으로 막힌 지점 없음." Do not manufacture a pattern that isn't there.

## 개념 간 연결
1-3 sentences on concepts that appeared in multiple entries, or that entries explicitly linked via their "연결된 개념" section. Omit this section entirely if no such connections exist.

Rules:
- Every date, topic, concept name, and claim must trace back to something literally stated in {til_entries}.
- The table covers the day-by-day view — the prose sections must synthesize across days, not repeat the table in sentence form.
- No embellishment, no motivational framing, no invented takeaways.
- Write entirely in Korean.
