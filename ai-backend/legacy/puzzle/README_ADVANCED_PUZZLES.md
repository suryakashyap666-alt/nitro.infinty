# Advanced Puzzle Solving (Nitro Infinity AI)

This folder will evolve the current lightweight `PuzzleEngine` into an image+text+voice capable puzzle solver with global adaptive learning.

## Current state (in repo)
- `backend/puzzle/puzzle_engine.py` exists.
- It supports basic type detection from **text** and a **global shared memory** lookup.
- It provides a failsafe step-by-step reasoning plan and hint mode.

## Next milestones
1. Wire `PuzzleEngine` deeper into `CoreBrain` with bot gating via `educationEnabled`.
2. Add backend endpoints for multipart image upload (and later OCR extraction).
3. Expand global memory: store CASE1/2/3 learning payloads and add similarity matching.
4. Add frontend UI for image/screenshots upload and display of hints/steps.

