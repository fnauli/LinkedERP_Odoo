# Kling AI runbook – Video 1 "The Human Algorithm" (human act only)

Goal: regenerate only the ~14 s human act (alley walk → arrival → handover) in Kling
as stylized 3D animation. Everything else (GPS act, captions, tags, PAKET DITERIMA
badge, recap, logo, music) stays from v8 and is composited afterwards in Claude Code.

**Never ask Kling for:** text, the H8KI logo, the GPS screen, the badge or the recap.

---

## Files in this folder

| File | Use |
|---|---|
| `courier_ref_back.png`, `courier_ref_side.png` | Character references for Kling's **Element Library** (bind as subject "KURIR") |
| `clip1_establishing_start.png` | Start frame, clip 1 |
| `clip2_tracking_start.png` | Start frame, clip 2 |
| `clip3_arrival_start.png` | Start frame, clip 3 |
| `clip4_handover_start.png` | Start frame, clip 4 (**generate this first as the test**) |

All frames are 1080×1920 (9:16), with no text and no logos.

---

## Settings (every clip)

- Mode: **Image to Video**
- Model: newest Kling model available on your plan
- Aspect ratio: **9:16**
- Duration: **5 s** (longer clips drift)
- Quality: **Professional / High quality**
- Creativity vs. relevance: lean toward **relevance** (stay close to the image)
- Upload the matching start frame; bind the KURIR element where the option exists
- Generate 2–4 variations per clip and keep the best one

**Negative prompt (paste into every clip):**

```
changing clothing, changing hairstyle, different face, extra limbs, deformed hands, extra fingers, text, letters, words, watermark, logo, signage text, jittery motion, warping, morphing, flickering, camera shake
```

**Character block (included in each prompt below):**

```
[KURIR]: young Indonesian male courier, mid-20s, slim build, dark navy uniform jacket with thin red and green trim, red cap, dark trousers, large red rectangular delivery backpack with a plain white label panel, carrying a small red parcel
```

---

## Clip 4 – handover (do this one first)

Start frame: `clip4_handover_start.png`

```
[KURIR]: young Indonesian male courier, mid-20s, slim build, dark navy uniform jacket with thin red and green trim, red cap, dark trousers, large red rectangular delivery backpack with a plain white label panel. He holds out a red parcel with both hands to a young woman in a beige hijab and long plum dress standing in a brightly lit doorway of a green-painted house; she smiles and receives it with both hands, he gives a small polite nod. Medium shot from the side, warm golden light from the doorway falls on both of them, cool blue night around. Camera nearly still with a very slow push in. Stylized 3D animation, Pixar-like, soft cinematic lighting, natural easing, gentle cloth and hijab movement.
```

If the hands break, regenerate. If it still fails after 4 attempts, keep v8's handover and use Kling only for clips 1–3.

## Clip 1 – establishing

Start frame: `clip1_establishing_start.png`

```
[KURIR]: young Indonesian male courier, mid-20s, slim build, dark navy uniform jacket with thin red and green trim, red cap, dark trousers, large red rectangular delivery backpack with a plain white label panel, carrying a small red parcel. He walks slowly away from camera down a narrow Indonesian kampung alley at night, crescent moon, warm wall lamps glowing, a mosque dome in the distance, a sleeping cat on a low wall. Camera slowly pushes forward following him from behind. Stylized 3D animation, cinematic night lighting, deep blue shadows with warm amber highlights, light mist, shallow depth of field.
```

## Clip 2 – tracking

Start frame: `clip2_tracking_start.png`

```
[KURIR]: young Indonesian male courier, mid-20s, slim build, dark navy uniform jacket with thin red and green trim, red cap, dark trousers, large red rectangular delivery backpack with a plain white label panel, carrying a small red parcel. He walks steadily through the alley seen from behind, natural walk with weight shift, the red backpack swaying gently with each step, a mango tree overhanging the wall, moths around a warm streetlamp. Camera tracks smoothly behind him at walking pace, background softly blurred. Stylized 3D animation, warm cinematic night lighting.
```

## Clip 3 – arrival

Start frame: `clip3_arrival_start.png`

```
[KURIR]: young Indonesian male courier, mid-20s, slim build, dark navy uniform jacket with thin red and green trim, red cap, dark trousers, large red rectangular delivery backpack with a plain white label panel, holding a small red parcel. He stops at a black iron gate in front of a green-painted house next to a small shuttered warung and presses the doorbell on the gate pillar. A moment later a warm golden porch light glows on and spills across the pavement. Camera slowly pushes in. Stylized 3D animation, warm light against cool blue night.
```

---

## Budget check

4 clips × about 3 generations = about 12 generations of 5 s each. Try cheaper/standard
mode first while learning, and switch to Professional only for the keeper takes.

## When you're done

Download the four keeper clips (MP4, highest quality) and upload them to this chat,
named `clip1.mp4` … `clip4.mp4`. Claude Code will then:

1. trim and order them, matching the cut points of v8,
2. grade them to H8KI brand colours (red #FE0000, green #039844, navy #291B73),
3. composite the logo label on the bag where it reads, plus all Indonesian text, the
   location tags, the PAKET DITERIMA badge, the recap and the end card,
4. reuse the existing v8 GPS act and the licence-free soundtrack, re-timed to the new cuts,
5. deliver a finished 9:16 MP4 under 35 s, with nothing important below y=1500.
