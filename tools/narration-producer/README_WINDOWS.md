# Tomb World Narration Producer for Windows

## ONE-TIME SETUP

1. Install Python 3 for Windows.
2. Make sure "Add Python to PATH" is enabled during installation if offered.
3. Pull the latest TombWorldSoloGuide using GitHub Desktop.
4. Double-click SETUP_NARRATION_PRODUCER.bat.
5. Paste the ElevenLabs API key after:
   ELEVENLABS_API_KEY=
6. Save and close Notepad.

## NORMAL USE

1. Pull the latest repository in GitHub Desktop.
2. Double-click RUN_NARRATION_PRODUCER.bat.
3. The Narration Producer opens automatically.
4. Choose voice/model/settings.
5. Select narration.
6. Dry Run Selected.
7. Review the plan.
8. Generate only when intentionally ready.
9. Close the command window when finished.
10. Use GitHub Desktop to review, commit, and push generated files.

`127.0.0.1` means the Producer is running only on your own computer. It is not exposed to your network or the public web. Dry Run does not contact text-to-speech or consume speech credits. The API key stays in the ignored local `.env` file and is never sent to the browser.
