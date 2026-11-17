This is the documentation for how the next step of designing the UI, restructuring tabs should go about.

The tab "Soạn đề" becomes the ultimate screen. Other tabs "Chào thầy cô" and "Tủ đề" merely become features of "Soạn đề". From now on, I will call "Soạn đề" as "the workspace", or "the main workspace". The "workspace" is everything on the screen that is not on the sidebar (assuming there are no settings windows); and the screen is the sidebar + the workspace.

DO NOT CHANGE ANYTHING ABOUT THE CURRENT WORKSPACE. ALL MODIFICATIONS SHOULD BE MADE **AROUND** THE WORKSPACE, RATHER THAN DIRECTLY ONTO IT.

1. How "Chào thầy cô" would be integrated into the main workspace:
- Upon loading up, the user is already met with the main workspace.
- Upon loading up, the workspace contains the line "Chào thầy cô ...", with the ASTRA logo above it, similar to how it is currently over at "Chào thầy cô" tab. This line is the big tagline in the middle of the workspace.
- When other components are done loading in, two buttons appear (with a subtle upwards float-in animation) side-by-side below the tagline: "Soạn từ mẫu", and "Soạn chi tiết", similar to how it is currently at the intermediary window between "Chào thầy cô" and "Soạn đề". 
- At the same time, the prompt bar also appears (also with the float-in animation) below the two Soạn buttons. This is so that it is UNMISSABLE.
- When an exam starts to generate, the "Chào thầy cô" elements disappear (with a subtle upwards float-out animation), the prompt bar sweeps to the correct position (that of the current "Soạn đề" tab), then the chat and the exam panel appears (also with the float-in animation).

2. How "Tủ đề" would be integrated into the main workspace:
- Tủ đề would entirely be confined within the sidebar.
- The sidebar can eliminate the buttons "Chào thầy cô", "Soạn đề", and "Tủ đề" now, since they are all fully integrated.
- The sidebar now consists of these new options:
    + Tạo đề mới, which when clicked, brings the user back to the integrated "Chào thầy cô" screen.
        * This feature has an icon to the left of it.
    + Tủ đề
        * List of exams. Each exam will have an icon, that:
            * Is aligned horizontally with the exam name, and aligned to the right of the sidebar.
            * Displays the status of the exam: Generating (spinner), Flagged (flag), Error (cross), Done (immediately after the exam is completed, plays animation of a tick appearing, then disappearing; after that, no icon).
    + The icons SHOULD NOT be any taller than the text themselves (as not to cause dead-space-clutter)