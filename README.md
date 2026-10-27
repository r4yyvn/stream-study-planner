# Stream & Study Planner

A weekly timetable for your streams and study sessions. It shows what's on now, counts down to the next block, and adds up your hours for the week.

- **On your PC:** double-click `Start planner.bat`. The planner opens in your browser and you can edit it. Keep the black window open while you edit.
- **On your phone:** open your GitHub Pages link (`https://YOUR-USERNAME.github.io/stream-study-planner/`). It works when your PC is off. The phone copy is view-only.
- **With Claude:** open this folder in Claude Code and ask, for example, "move Friday's stream to 9 PM". Claude edits `schedule.json` and publishes it.

Your schedule lives in `schedule.json`. After you edit on the PC, the planner publishes the changes to GitHub on its own about 15 seconds later. Your phone shows them within a few minutes; pull down or tap **Refresh** to reload.

## One-time setup for the phone link

1. Install **Python** (already done on this PC) and **Git for Windows** from https://git-scm.com/download/win. Keep the default options.
2. Make a free account at https://github.com if you don't have one.
3. On GitHub, create a new **public** repository named `stream-study-planner`. Leave it empty (no README).
4. Ask Claude to "connect the planner to my GitHub repo". Claude links this folder to the repository and makes the first upload. A browser window asks you to sign in to GitHub the first time.
5. On GitHub, open the repository, then **Settings → Pages**. Under "Branch", choose `main` and `/ (root)`, then **Save**. After a minute or two, the page shows your link.
6. Open that link on your phone and add it to your home screen.

**Privacy:** a GitHub Pages site on a free account is public. Anyone who has the link can see your schedule, so don't put private details in the notes.

## schedule.json format

```json
{ "id": "mon-stream", "day": "Mon", "start": "19:00", "end": "22:00",
  "type": "stream", "title": "Valorant ranked", "tag": "Twitch",
  "notes": "", "doneWeek": "" }
```

- `day`: Mon, Tue, Wed, Thu, Fri, Sat or Sun
- `start` / `end`: 24-hour times; use `24:00` for midnight at the end of the day
- `type`: stream, study, break or other
- `doneWeek`: the week it was ticked done, like `2026-W44`; it resets on its own each week
- `example: true` marks the sample blocks; **Clear examples** removes them
