# Printable agenda specification

## Deliverables and dates

- Create separate files named `Samuel-Agenda-YYYY-MM-DD.docx` and
  `Chasen-Agenda-YYYY-MM-DD.docx`.
- Publication is immutable. If that filename already exists with different
  bytes, publish `-r2`, `-r3`, and so on; never overwrite and recite a previously
  delivered path. An identical existing file may be reused.
- Validate and render the complete Samuel-and-Chasen batch before copying either
  document into the shared destination.
- Target dates are Monday, Wednesday, or Friday.
- Monday and Friday files are two pages: child agenda first, child-specific
  parent report second. Wednesday files are one page.
- Use the header `Name - Weekday, Month Day, Year`.

## Page 1 order

1. Morning Checklist
2. School
3. Fine Arts
4. Physical Education
5. Afternoon Checklist

Use a grayscale-friendly US Letter portrait form: black text, light-gray section
bands, dark borders, prominent checkboxes, and writable fields. Use the
`compact_reference_guide` document preset with a named `printable_agenda_form`
override for printer-safe compact margins and grayscale-only styling.

## Routine content

Morning has separate checkboxes:

- Make your bed
- Pick up trash around your room
- Get dressed

School uses one checkbox row per subject. Print only the exact ClassReach course
name and its assignment count, using `1 assignment` or `N assignments`. Do not
print assignment titles, instructions, details, handouts, or messages on the
child agenda. Check and strike the subject row only when every assignment for
that subject is complete.

Include a separate unchecked `Bible` row even when ClassReach lists no Bible
assignments for the day. Do not double-print Bible if it already appears among
the assignment-bearing subjects.

Fine Arts and Physical Education lines also have checkboxes. Every time field
asks for minutes.

Samuel:

- Monday: Percussion Lesson; Percussion Practice
- Wednesday and Friday: Percussion Practice

Chasen:

- Monday: Trumpet Lesson; Trumpet Practice; Theater Class; Theater Practice
- Wednesday and Friday: Trumpet Practice; Theater Practice

Physical Education has one line every day with fields for activity and minutes.

Monday and Wednesday afternoon:

- Tidy your room and help tidy the house
- Prepare for school tomorrow
- Make your lunch

Under school preparation, include only exact ClassReach text that is useful for
the following Tuesday or Thursday: items to bring, unusual schedule/dress,
required materials, advance reading, deadlines, or special instructions. Do
not reproduce the next day's ordinary assignment list. If none exist, say
`No special ClassReach prep notes found`.

Do not discard a next-day task merely because its text is very short. Preserve
terse actionable text such as `Bible`. Also extract an exact materials sentence
from an otherwise in-class item when it identifies something the student must
have available, such as a spiral notebook.

The preparation classifier must account for every selected-date item using one
of: `actionable_preparation`, `required_material`, `ordinary_in_class`,
`optional`, or `informational`. Unknown item types fail closed. A no-preparation
claim is valid only when neither of the first two classifications remains.

Wednesday also includes:

- Samuel: Gather the towels for laundry
- Chasen: Gather the family trash

Friday afternoon:

- Tidy your room and help tidy the house
- Put your school stuff away

Friday has no lunch or next-day-school preparation item.

At the bottom of page 1, add an `Additional Tasks` section with three blank
checkbox lines for the child to write in.

## ClassReach fidelity

- Every ClassReach-derived field must originate from typed `classreach` CLI
  output. Keep the raw JSON response in the run's temporary workspace long
  enough to verify normalization, then remove or retain it according to the
  user's data-handling request. Do not use browser-derived content.

- Preserve exact course names, displayed order, assignment counts, and aggregate
  completion state.
- Use one checkbox per subject. Check and strike only when every assignment for
  that subject is complete.
- If no assignments genuinely exist, print `No assignments listed in
  ClassReach` and `Checked on <timestamp>`.
- Relevant extras are assignment-linked material plus new/unread messages and
  discussions since the prior printed agenda. Exclude stale standing handouts
  and unrelated school-wide material.
- Keep assignment titles, details, and relevant extras out of the child agenda;
  they may still appear where required in the parent report.
- Use hyperlinks behind descriptive text when a stable source URL is available;
  do not print long opaque URLs.

## Parent reports

Always include page 2 on Monday and Friday, even when every category says
`Nothing to report`.

Monday reports:

- week-ahead schedule or agenda changes;
- special materials or events;
- important new/unread messages and discussions;
- unresolved assignments carried over from the prior school week.

In the `Incomplete work` section, group unresolved assignments by subject and
print only the exact subject name plus assignment count. Do not print assignment
titles, weekdays, instructions, or details there. Messages and schedule notices
remain separate non-assignment items.

Friday reports:

- still-unchecked ClassReach assignments from Monday through Thursday only;
- important new/unread messages, discussions, and handouts from the week;
- explicit schedule or agenda-change notices.

Do not treat Friday's new assignments as overdue when generating Thursday
night. Report only explicit change notices or items ClassReach identifies as
updated; do not retain hidden raw-data snapshots solely to calculate diffs.

## Normalized JSON input

`scripts/build_agendas.py` accepts one child per invocation:

```json
{
  "student": "Samuel",
  "date": "2026-08-19",
  "checked_at": "2026-08-18 8:30 PM ET",
  "courses": [
    {
      "name": "Exact Course Name",
      "assignment_count": 2,
      "completed_count": 1,
      "handouts": true,
      "messages": false,
      "url": "https://...",
      "assignments": [
        {
          "title": "Exact assignment title",
          "details": "Exact ClassReach details",
          "completed": false,
          "url": "https://..."
        }
      ]
    }
  ],
  "classreach_extras": [
    {"course": "Course", "type": "Handout", "title": "Exact title", "details": "", "url": "https://..."}
  ],
  "next_day_prep": [
    {"course": "Course", "text": "Exact ClassReach text", "url": "https://..."}
  ],
  "parent_report": {
    "incomplete": [],
    "messages": [],
    "changes": []
  }
}
```

Omit `parent_report` on Wednesday. Use empty arrays only after verifying that
the source category is genuinely empty.

## Publication manifest

The immutable publisher writes one content-free JSON manifest beside each
DOCX. It records the student, date, published filename, normalized-input hash,
DOCX hash, page count, and page-image hashes. It must not contain assignment,
message, discussion, or student-source text.
