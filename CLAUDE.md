# Stream & Study Planner

The user's weekly streaming and study timetable. `index.html` is the planner page, `schedule.json` is the data, and `server.py` (started by `Start planner.bat`) is the local helper used to edit on the PC. The folder is a git repo; GitHub Pages serves a read-only copy the user opens on their phone.

## Changing the schedule when the user asks

1. Edit `schedule.json` directly. The format is in README.md. Keep `day` as Mon–Sun, times as `HH:MM` (24h, `24:00` allowed as an end), `type` one of stream/study/break/other. Give new blocks a short unique `id`. Keep blocks sorted by day, then start time. Keep the JSON valid.
2. Set `updated` to the current UTC time (`YYYY-MM-DDTHH:MM:SSZ`).
3. Publish: `git add schedule.json`, `git commit -m "<short description>"`, `git push`. The phone link updates within a few minutes.

If the user has the planner open on the PC, tell them to reload it after you change the file, so an edit from the open page doesn't overwrite yours.

Only change `index.html` or `server.py` when the user asks for a change to how the planner works.
