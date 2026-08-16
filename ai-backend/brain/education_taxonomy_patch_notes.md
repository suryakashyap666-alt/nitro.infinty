(Internal) Notes
- Implement universal education taxonomy + subject matching.
- LearningEngine now supports per subject_id adaptation (weak/strong, speed proxy, learning style).
- CoreBrain adds missing handler methods: _teach_subject/_quiz_subject/_worksheet_subject/_studyplan_subject.
- Quiz/worksheet correctness updates: generated questions return an expected answer key; parsing uses heuristic + uses '#answer ... correct:true/false' from user.

