# Kling motion prompts – Video 1 "The Human Algorithm" (realistic version)

Settings for every clip: Video Generation · VIDEO 3.0 · start frame from History · end frame EMPTY ·
1080p · 5 s · 1 output · Native Audio OFF · Multi-Shot OFF.
Clips 1–3: bind KURIR REAL only. Clip 4: bind KURIR REAL + WARGA.

---

## Clip 4 – Handover (generate first)

```
Photorealistic cinematic live-action shot, continuing exactly from the start image: same two people, same faces, same clothes, same green house, same black iron gate, same night lighting.

Action, in order over five seconds: the courier and the woman are both holding the small plain red parcel at chest height. The courier smiles warmly and gently lets go, sliding his hands away from the box. The woman takes the full weight of the parcel and draws it toward her chest with both hands, holding it close. She smiles with genuine gratitude and gives a small, polite nod of thanks. The courier returns a small, respectful nod with a friendly smile and lowers his hands to his sides, relaxed.

Natural details: real weight in the parcel, fingers keep a firm natural grip, subtle breathing, natural blinks, soft eye contact between them. Her beige hijab drapes and moves softly with the nod. His jacket creases naturally, the red backpack settles slightly on his shoulders.

Camera: locked-off medium shot from the side, almost still, with a very slow, smooth push-in. Lighting: warm golden light from the porch lamp and the house falls on both faces, cool deep-blue night around them, gentle highlights on the red parcel.

Look: shot on ARRI Alexa, 50mm lens, shallow depth of field, natural skin texture, true-to-life colour, subtle film grain, 24fps cinematic motion blur, smooth realistic movement.

Avoid: changing faces, morphing, changing clothes or hijab colour, extra or missing fingers, hands merging with the box, the parcel changing shape or colour, a ribbon or bow, text, letters, logos on the bag label, warping background, flicker, jitter, camera shake, sudden cuts.
```

## Clip 1 – Establishing

```
Photorealistic cinematic live-action shot, continuing exactly from the start image: same courier seen from behind, same misty kampung alley at night, same lamps, same distant mosque.

Action over five seconds: the courier walks slowly away from the camera down the middle of the alley at a calm, steady pace, with a natural relaxed gait. Each step shows real weight: heel strike, slight shoulder sway, gentle vertical bob. His arms swing naturally, one hand loosely holding the small red parcel. The large red delivery backpack bounces and sways slightly with every step, a beat behind his body.

Environment motion: soft haze drifts slowly through the warm lamplight, the wall lamps glow with a faint natural flicker, tiny dust specks float in the light, the distant mosque dome glows softly through the mist, the cat sleeping on the low wall stays asleep and breathes slowly. Damp ground catches small reflections of the lamps as he passes.

Camera: wide shot from behind at walking height, following him with a slow, smooth, steady push-in, like a gimbal or dolly. The courier stays centred and gradually grows slightly larger in frame.

Look: shot on ARRI Alexa, 35mm lens, shallow depth of field, deep blue night with warm tungsten highlights, true-to-life colour, subtle film grain, 24fps cinematic motion blur.

Avoid: the courier turning around, changing clothes or cap colour, extra limbs, warping walls, morphing, text, letters, logos on the white bag label, flicker, jitter, camera shake, sudden speed changes.
```

## Clip 2 – Tracking

```
Photorealistic cinematic live-action shot, continuing exactly from the start image: same courier from behind, same alley, same mango tree with yellow mangoes, same lamp.

Action over five seconds: the courier keeps walking steadily forward, away from camera, with natural weight shift from foot to foot, relaxed shoulders, a small natural sway of the hips. The red delivery backpack sways and settles with each step, the straps tighten and loosen slightly. He holds the small red parcel securely at his side.

Environment motion: the mango leaves above sway gently in a light night breeze, the yellow mangoes rock slightly on their stems, two small moths flutter in irregular loops around the warm wall lamp, soft haze drifts in the background, the lamplight shimmers subtly on the walls.

Camera: medium shot, tracking smoothly behind him at the same walking pace, with a slight lateral drift for depth and gentle parallax between the foreground leaves and the background walls. Background softly blurred.

Look: shot on ARRI Alexa, 35mm lens, shallow depth of field, cool blue night with warm amber lamp highlights, true-to-life colour, subtle film grain, 24fps cinematic motion blur.

Avoid: the courier turning around, more insects or butterflies, mangoes growing or multiplying, changing clothes, extra limbs, morphing, warping, text, letters, logos on the white bag label, flicker, jitter, camera shake.
```

## Clip 3 – Arrival

```
Photorealistic cinematic live-action shot, continuing exactly from the start image: same courier in side view, same green house, same black iron gate between green pillars, same shuttered warung on the right.

Action, in order over five seconds: the courier presses the doorbell button on the gate pillar with his finger and holds it for a moment, then lowers his hand and waits patiently, adjusting the small red parcel in his other hand and glancing toward the front door with a hopeful, friendly expression. After a short pause, warm light switches on behind the windows of the house, and the wooden front door begins to open slowly, letting golden light spill out across the small front yard toward the gate and onto the courier.

Natural details: subtle breathing, a natural blink, the backpack settles slightly as he shifts his weight, a faint moth near the porch lamp.

Camera: medium shot from the side at chest height, slow smooth push-in toward the courier and the gate. Lighting: begins cool blue with the warm porch lamp, and becomes warmer and brighter as the house lights come on.

Look: shot on ARRI Alexa, 35mm lens, shallow depth of field, true-to-life colour, subtle film grain, 24fps cinematic motion blur.

Avoid: changing face, changing clothes, the parcel disappearing, extra fingers, the gate or pillars warping, signs with text or letters, logos on the white bag label, flicker, jitter, camera shake, sudden cuts.
```

---

## When a clip comes out wrong

| Problem | Fix |
|---|---|
| Face changes or morphs | Regenerate; check that KURIR REAL (and WARGA for clip 4) is bound |
| Hands or parcel break (clip 4) | Regenerate; if it fails 3 times, shorten the action: "she takes the parcel and smiles" |
| Too little motion | Add at the start: "Clear, visible motion throughout the shot." |
| Too much or jittery motion | Remove the environment-motion paragraph and keep only action + camera |
| Text appears on the bag | Regenerate; the logo is added later in post |

---

# v2 prompts for clips 2 and 3 (after reviewing clip 4 and clip 1)

Lessons applied: the steady-camera line worked in clip 1, so it is kept and made more precise. Clip 4's
camera drifted and cut a person off, so framing is now locked explicitly. Clip 1 invented letters on the
bag label, so the label instruction is now stronger (the logo is still composited in post). Clip 3 now
states that nobody appears in the doorway yet, so Kling does not invent a different woman.

## Clip 2 – Tracking (v2)

```
Steady, smooth tracking camera at constant distance; the courier stays centred and the same size in frame for the whole shot; no zoom, no sudden moves. Photorealistic cinematic live-action shot, continuing exactly from the start image: the same young Indonesian courier seen from behind (red cap, dark navy jacket, dark cargo trousers, black sneakers, large red delivery backpack with a plain white label, small red parcel in his right hand), the same narrow kampung alley at night, the same mango tree with yellow mangoes overhead, the same warm wall lamps.

Action over five seconds: he keeps walking forward at a calm, steady pace, away from the camera. Real walking mechanics: weight shifts from one foot to the other, heel strike then toe-off, relaxed shoulders, a gentle natural sway of the hips, arms moving slightly. The red backpack sways and settles with each step a fraction behind his body, the straps flex slightly. The parcel stays securely in his right hand the whole time.

Environment motion, subtle and natural: mango leaves sway softly in a light night breeze, the yellow mangoes rock gently on their stems, exactly two small moths flutter in slow irregular loops around the warm lamp, a thin haze drifts in the background, lamplight shimmers faintly on the old walls and the damp path.

Camera: medium shot from behind at shoulder height, gliding forward at exactly his walking speed like a gimbal, with a very slight sideways drift that creates gentle parallax between the foreground leaves and the background walls. Background softly out of focus, the courier sharp.

Look: shot on ARRI Alexa, 35mm lens, shallow depth of field, cool blue night with warm amber lamp highlights, true-to-life colour, natural contrast, subtle film grain, 24fps cinematic motion blur.

The white label on the backpack stays completely blank: plain white fabric with no letters, numbers, symbols or markings at any moment.

Avoid: the courier turning around or stopping, changing clothes, cap or backpack colour, the parcel disappearing or changing hands, extra limbs, morphing, more insects, butterflies, birds, mangoes growing or multiplying, warping walls, any text or logos anywhere, flicker, jitter, camera shake, zooming.
```

## Clip 3 – Arrival (v2)

```
Locked composition with only a very slow, subtle push-in; the courier, the doorbell on the gate pillar and the front door stay fully in frame for the whole shot; no pan, no sudden moves. Photorealistic cinematic live-action shot, continuing exactly from the start image: the same young Indonesian courier in side view facing right (red cap, dark navy jacket with thin red and green piping, dark cargo trousers, large red delivery backpack with a plain white label, small red parcel held in his left hand), the same green-painted house, the same black iron gate between green pillars, the same wooden front door, the same warm porch lamp, the same shuttered warung on the right, at night.

Action, in order over five seconds. From 0 to 1.5 seconds: he presses the doorbell button on the gate pillar with his right index finger and holds it briefly. From 1.5 to 3 seconds: he lowers his hand and waits patiently, shifting his weight slightly, adjusting the parcel in his left hand, and glances toward the front door with a calm, friendly, hopeful expression. From 3 to 5 seconds: warm light switches on behind the windows of the house, and the wooden front door slowly opens inward, letting soft golden light spill across the small front yard, through the gate and onto the courier's face and jacket. Nobody is visible in the doorway yet, only the warm light.

Natural details: subtle breathing, one natural blink, the backpack settles slightly as he shifts his weight, a single small moth near the porch lamp, faint haze in the cool night air.

Lighting: begins as cool blue night with the warm porch lamp, then becomes warmer and brighter on the courier as the house lights come on and the door opens. Skin tones stay natural.

Look: shot on ARRI Alexa, 35mm lens, shallow depth of field, true-to-life colour, natural contrast, subtle film grain, 24fps cinematic motion blur.

The white label on the backpack stays completely blank: plain white fabric with no letters, numbers, symbols or markings at any moment.

Avoid: changing face or identity, changing clothes, the parcel disappearing or changing hands, extra or missing fingers, a person appearing in the doorway, the gate, pillars or door warping, signs with text or letters, any text or logos anywhere, flicker, jitter, camera shake, panning, sudden cuts.
```
