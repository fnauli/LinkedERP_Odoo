# Clip 4 face fix – one courier from clip 1 to clip 4

## What is wrong

The courier in clips 1–3 matches the chosen portrait (01_courier_front_PICK): a slim face, tan skin, a
thin moustache and a small chin goatee. The clip 4 start frame (SF4_handover_PICK) came out with a
different man: younger, lighter skin, clean-shaven. Kling copied that face into clip 4.

The fix is to regenerate only the clip 4 start frame, using the right face, and then clip 4 itself.
Clips 1–3 stay as they are. Cost: 1 image generation and 1 video generation.

Swapping the face in post is not a good option. It needs face-swap models, which this environment
cannot download, and at this size it tends to look blurry and flicker, which is the AI look we are
removing.

## Files in this folder

| File | Use |
|---|---|
| `face_ref_A_front.jpg` | Full chosen portrait (watermark strip cropped). Main face reference. |
| `face_ref_B_front_closeup.jpg` | Close-up of the same face |
| `face_ref_C_clip3_frame.jpg` | Clip 3 frame: the same man in side view, same light as the handover |
| `face_ref_D_clip3_closeup.jpg` | Close-up of the clip 3 face (side view, what clip 4 needs) |

## Step 1 – New start frame (IMAGE 3.0)

1. Go to Image Generation → IMAGE 3.0, aspect ratio 9:16, 4 outputs.
2. Bind the elements **KURIR REAL** and **WARGA**, the same as before.
3. If the KURIR REAL element was built from the clean-shaven face, open it first. Use **Add image** to add
   `face_ref_B_front_closeup.jpg` and `face_ref_D_clip3_closeup.jpg`, and remove any clean-shaven image.
4. Image Reference: upload `SF4_handover_PICK.webp` (in `../selected/`). Use the composition/scene
   reference only, not face or subject, at low to medium strength, so it keeps the layout but not the old face.
5. Prompt:

```
Photorealistic cinematic night photo, 9:16. In front of a green-painted house with a black iron gate between green pillars and a warm porch lamp, an Indonesian delivery courier and a young woman stand facing each other, both holding a small plain red parcel at chest height, both smiling warmly. Side view, the courier on the left facing right, the woman on the right facing left.

The courier: Indonesian man about 28 years old, slim face with defined cheekbones, warm tan brown skin, a thin neat moustache and a small short goatee on the chin, short black hair under a red baseball cap, dark navy uniform jacket with thin red and green piping, dark cargo trousers, a large red delivery backpack with a plain blank white label on the back. Exactly the same man as the reference portrait.

The woman: beige hijab, long plum dress, gentle smile, exactly as the WARGA reference.

Lighting: warm golden porch light on both faces, deep blue night around. Shot on ARRI Alexa, 50mm, shallow depth of field, natural skin texture, true-to-life colour.
```

6. Negative prompt (if the field is shown):

```
clean-shaven, no facial hair, baby face, teenager, pale skin, different face, text, letters, logo on the bag label, ribbon, bow, extra fingers, deformed hands
```

7. Choose the image whose courier **clearly has the moustache and goatee**, with the same parcel position and
   a white label visible on the bag. Compare it side by side with `face_ref_D_clip3_closeup.jpg`. Send me
   the four results if you are unsure.

## Step 2 – Regenerate clip 4 (VIDEO 3.0)

Use the same settings as before: Video Generation · VIDEO 3.0 · 1080p · 5 s · 1 output · Native Audio
OFF · end frame empty · bind KURIR REAL + WARGA. The start frame is the new image from step 1.

Use the clip 4 prompt from `../KLING_MOTION_PROMPTS.md`, with one line added at the very start:

```
The courier keeps exactly the same face throughout: slim face, tan skin, thin moustache and small chin goatee, as in the start image.
```

and add to the Avoid line: `the courier becoming clean-shaven or younger, the face changing`.

## Step 3 – Send it back

Download it without a watermark and upload it here as `clip4_handover_take2.mp4`. I will re-cut it into
the same 4-second slot. The H8KI logo tracking, captions, badge and timing will be re-applied automatically.
