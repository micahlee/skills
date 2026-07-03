---
name: workout-prep
description: Generate Micah's structured workout warmups and cooldowns from Fitbod screenshots, workout exercise lists, or "/workout-prep" requests, using a 3-move warmup cycled 2x and 3 cooldown stretches with image searches, coaching rationale, and optional Fitbod entry guidance.
---

# Workout Prep

## Purpose

Create tailored warmup and cooldown guidance for Micah's push/pull/legs workouts. Use this for Fitbod screenshots, copied workout lists, or explicit `/workout-prep` requests.

## Response Shape

1. Start with 1-2 sentences identifying the day's focus and what makes the workout demanding or unique.
2. Add `---`.
3. Add `## Warmup — 2 rounds`.
4. Give 3 numbered moves.
5. For each move, run an image search before writing the move, then include the image inline immediately before the bold move name when images are available.
6. Under each move, write 1-2 flowing sentences explaining why it fits the specific workout.
7. Add `---`.
8. Add `## Cooldown Stretches — hold 30-45 sec each`.
9. Give 3 numbered stretches with the same image-before-description structure.
10. Close with one specific encouraging line that names the most important warmup/cooldown move or sleeper-difficult exercise for that day.

Avoid bullet lists inside move rationales. Do not add generic disclaimers unless the user mentions pain, injury, medical constraints, or unusual symptoms.

## Exercise Selection

Choose moves based on the workout's loaded patterns.

Always include Micah's PT-prescribed **Rotator Cuff Eccentrics** drill in the warmup. Source video: https://youtu.be/FVkmcdtwwPw?si=VV6lMCcoYPctYTCE. Treat this as one of the 3 warmup moves unless the user explicitly asks for an expanded warmup, and choose the other 2 warmup moves around the day's main loaded patterns. Use the video link as the inline reference for the move when helpful, and explain it as shoulder/rotator-cuff prep from physical therapy rather than as a generic optional shoulder exercise.

For push days, prioritize shoulder/scap prep, thoracic mobility, pressing groove, chest/tri cooldown, and shoulder/triceps recovery.

For pull days, always include **External Rotations - Elbow on Knee** as a workout move unless the user explicitly says to skip it. Source video: https://youtu.be/_bezkjZIa-A?si=68TeME2PeDT4jDHD. Treat it as Micah's PT-prescribed pull-day rotator-cuff accessory, distinct from the 3-move warmup. If giving Fitbod entry guidance, first suggest searching Fitbod for `External Rotation`, `Dumbbell External Rotation`, or `Elbow on Knee External Rotation`; if no matching catalog exercise exists, suggest adding it as a custom/manual exercise. For the rest of pull-day prep, prioritize hangs or lat opening, scapular retraction/depression, thoracic extension, biceps/forearms, lats, and lower-back decompression.

For leg days, prioritize hips, ankles, glutes, hinge/squat patterning, calves, hamstrings, quads, and hip flexors.

For core-heavy work, include bracing or spinal-control prep and cooldowns that unload abs, hip flexors, and low back.

## Common Warmups

Upper body: Arm Circles, Band Pull-Apart, Scapular Push-Up, Band External Rotation, Dead Hang, Wrist Circles, Cat-Cow, Thoracic Rotation, Diamond Push-Up.

Lower body: Leg Swings, Hip Circles, Glute Bridge, Bodyweight Squat, Bodyweight Hip Hinge, Clamshell, Single Leg Hip Hinge, Bodyweight Walking Lunge, Bodyweight Good Morning, PVC Overhead Squat, Bodyweight Sumo Squat.

Core: Plank Hold, Bird Dog, Cat-Cow.

## Common Cooldowns

Upper body: Doorway Chest Stretch, Overhead Tricep Stretch, Cross-Body Shoulder Stretch, Wall Bicep Stretch, Doorway Lat Stretch, Child's Pose Lat Stretch, Prone Cobra.

Lower body: Standing Quad Stretch, Seated Hamstring Stretch, Lying Hamstring Stretch, Pigeon Pose, Figure-Four Stretch, Kneeling Hip Flexor Stretch, Wall Calf Stretch, Heel Drop Calf Stretch.

Spine/core: Supine Spinal Twist, Knees to Chest, Child's Pose, Prone Cobra.

## Fitbod Guidance

If the user asks about Fitbod entry, give practical instructions rather than assuming phone sync works.

- Mac Fitbod workouts can be read locally, and Mac UI automation can add a visible warmup section.
- Mac-generated workout edits did not reliably sync to the iPhone in testing.
- If the user works out from the phone, treat the phone workout as source of truth and provide concise manual entry instructions.
- Prefer Fitbod's UI path for active workouts: `Add Exercise` -> select 3 moves -> `Group as...` -> `Warm-up`.
- Avoid direct SQLite edits unless the user explicitly wants a careful experiment with backups.

## Tone

Be warm, practical, and coach-like without cheerleading. Mention progressions or sleeper-difficult moves when visible. Keep encouragement specific: "That dead hang is the one to not skip today" is better than generic hype.
