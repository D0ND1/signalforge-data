# signalforge-data (public repo kit)

Copy this folder's contents into a NEW PUBLIC GitHub repository (name suggestion: `signalforge-data`). Public repos get unlimited free
Actions minutes, so the daily snapshot costs $0 and runs when your laptop and server are off. The history it builds is the moat:
nobody can go back and collect yesterday's data later.

You do (2 minutes): create the empty public repo, upload these files, open the Actions tab, press "Run workflow" once.
It needs no secrets: the workflow uses the temporary token GitHub gives every run.

What it stores: official recall records (CPSC, FDA) and the latest release of each repo in `watch.json`, as dated JSON.
Terms: CPSC and FDA data are US government sources; openFDA says its data is unvalidated and not for medical decisions, so every public
page built from it must link the agency page and say "last checked <date>". GitHub release data is public metadata.
Subscription prices are NOT here yet: they are read from each service's own pricing page by the main pipeline (scout), and a
robots/terms check per site comes before any of that is mirrored publicly.
