# Hackathon Requirements & Submission Checklist

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 2. Verified hackathon requirements

Sources: [Overview](https://youcam-api-skin-ai-ecommerce.devpost.com/), [Official Rules](https://youcam-api-skin-ai-ecommerce.devpost.com/rules), [Schedule](https://youcam-api-skin-ai-ecommerce.devpost.com/details/dates), [Updates](https://youcam-api-skin-ai-ecommerce.devpost.com/updates), [Discussion forum](https://youcam-api-skin-ai-ecommerce.devpost.com/forum_topics), and the [Perfect Corp press release](https://www.perfectcorp.com/business/news/YouCam-API-Hackthon-eCommerce). All fetched 31 Oct 2026.

| # | Item | Verified finding | Status |
|---|---|---|---|
| 1 | Requirement | "Create a working application that integrates at least one Perfect Corp. YouCam API and demonstrate clear consumer or eCommerce value." It must install, run consistently and work as shown in the video. | [V] |
| 2 | Deadline | Submission period: 29 Sep 2026 12:00 ET → **2 Nov 2026 11:45 ET**. Registration closes at the same time. | [V] |
| 3 | Nigeria | **Eligible.** The excluded list is Afghanistan, Antarctica, Belarus, Brazil, China, Crimea, Cuba, Djibouti, Donetsk, Iran, Iraq, **Italy**, North Korea, Luhansk, Quebec, Russia, Somalia, Sudan, Ukraine, Venezuela, Vietnam, Western Sahara and OFAC-sanctioned countries. Nigeria is not on it. You must be above the age of majority where you live (18 in Nigeria). | [V] |
| 4 | Required API | **Any one** YouCam API. Judging text names the "Skin, Beauty, Fashion, Jewelry & Watch, Hair & Beard" categories. **Skin Analysis alone is sufficient.** VTO is optional. There are two topics: "Skin AI" (Skin AI alone *or* combined) and "eCommerce VTO". GlowCue fits **Skin AI**. | [V] |
| 5 | Available APIs | Skin Analysis (SD/HD), Fitzpatrick skin type, face analyser, makeup/hair/clothes/jewellery VTO, image and video generation, and more. See the [docs index](https://docs.perfectcorp.com/llms.txt). | [V] |
| 6 | Free units | **1,000 units per registrant.** Process: register on Devpost → redeem code arrives by email ("Start Kit") → create a YouCam API account → Account > Redeem Code. Codes are valid **90 days from redemption**. Optional social-sharing bonus: +500 units per platform, up to 2, claim form due by the deadline. | [V] |
| 7 | Judging | Stage 1: pass/fail on theme fit and API use. Stage 2: **four equally weighted criteria**: Technological Implementation, Design, Potential Impact, Quality of Idea. Ties are broken in that criterion order. | [V] |
| 8 | Submission materials | (a) Repo URL with all source, assets and instructions; public with a licence, or private shared with `testing@devpost.com`. **The 28 Oct update says private repos can't be reviewed, so make it public.** (b) Text description of features and consumer/eCommerce value. (c) **Screenshots.** (d) **1–3 min demo video** on YouTube (preferred) or Vimeo, public. It must explain which YouCam API is used, show the working product on its target device, and contain no third-party trademarks or copyrighted music without permission. (e) A test link: a working project, free and unrestricted, **until judging ends (20 Nov)**. | [V] |
| 9 | Prizes | 1st $2,500; 2nd $1,000; 3rd $500 (each with a feature blog post and a marketing meeting); Women in Tech $1,000; **Rising Star (student) $1,000**, which requires a team member who is enrolled and gives a **valid school-issued email** at submission. You opt into special awards when submitting. **Max one prize per project.** Winners must complete affidavits (W-8BEN for non-US), do an exit interview and agree to a blog article. | [V] |
| 10 | Disqualification | Ineligible residence; organiser affiliation; false eligibility info; IP infringement; non-original work; projects funded by or licensed from Perfect Corp; existing projects not "significantly updated"; failure to function as shown; tampering. Third-party APIs and data must be used within their licences. | [V] |
| — | Judge testing | **Clarified by the organiser on the forum (29 Oct):** a public build that **replays a recorded real API response, clearly labelled**, plus source and video, satisfies the testing requirement. "Please do not publish your API key." | [V] ([thread](https://youcam-api-skin-ai-ecommerce.devpost.com/forum_topics/45693-judge-access-local-test-build-with-recorded-api-result-and-gated-fresh-inference)) |
| — | Judging dates | The rules say 3–20 Nov; the schedule page says 9–20 Nov. **Keep the app live until at least 21 Nov.** Winners are announced around 24 Nov. | [V] |
| — | Language | English, or English translations of everything. | [V] |
| — | IP | You keep ownership. The sponsor gets a non-exclusive licence for judging and promotion. Open source is allowed if licences are honoured. | [V] |

**Discrepancies with your brief**
- **"Required API":** your brief implied a Skin Analysis vs VTO split. In fact *any* YouCam API qualifies, and VTO is not required.
- **"Student award":** it requires a **school-issued email at submission**, not just student status. A forum question about non-.edu addresses is still open **[U]**.
- **Bonus units:** the press release says up to 1,000 bonus units. The rules say 500 per platform, max 2. These agree.
- **Video hosts:** the overview page lists YouTube, Vimeo or Youku; the rules list only YouTube or Vimeo. Use **YouTube**, which is preferred and in both lists.
- **Forum reports:** redeem codes failed early in the hackathon ("does not exist", "reached maximum redemptions"). The organisers fixed both. **Redeem today** so there is time to email support if needed: `contact_event@PerfectCorp.com` (hackathon) or `YouCamOnlineEditor_API@perfectcorp.com` (API).

---

## 15. GitHub & documentation

- Repo: `github.com/<you>/glowcue`, **public**, MIT licence. MIT is compatible with the rules ("public with relevant licensing") **[V]**.
- **README sections:**
  1. Title + tagline + badges.
  2. Hero screenshot.
  3. Live demo link + YouTube link.
  4. The problem (3 lines).
  5. What GlowCue does (bullets).
  6. **How YouCam is used**: AI Skin Analysis v2.1 SD; endpoints; 10 concerns; raw vs ui score handling; masks; deletion.
  7. Architecture diagram.
  8. Recommendation engine summary.
  9. Run locally (mock mode needs no key) and enable live mode.
  10. Env vars table.
  11. Tests.
  12. Privacy & safety.
  13. Cosmetic disclaimer.
  14. Demo-catalogue disclaimer.
  15. Limitations (single photo, lighting, skin-tone performance not independently validated by us).
  16. Roadmap.
  17. Licence + acknowledgements (fonts, icons).
- Also commit: `.env.example` (both), `docs/ARCHITECTURE.md`, `docs/YOUCAM_NOTES.md`, `docs/screenshots/`, pinned `requirements.txt` and `package-lock.json`.
- **Secret check before the repo goes public:** `git log -p | grep -iE "bearer|youcam_api_key="` returns nothing except placeholders. If a key was ever committed, **rotate it in the console** (rewriting history isn't enough).
- **Never commit:** `.env`, the raw probe output (`fixtures/raw/`), or photos of anyone without consent.

---

## 21. Final definition of done & compliance checklist

**Product**
- [ ] Full journey works on the public URL: sample **and** live, desktop **and** phone.
- [ ] Live call uses YouCam Skin Analysis v2.1; the balance decreases as expected.
- [ ] Recommendations deterministic, explained, within budget or clearly flagged; AM/PM rules respected.
- [ ] Cart totals correct; checkout preview says no payment is taken.
- [ ] Disclaimers (cosmetic, not medical; demo catalogue) and the privacy notice are visible.
- [ ] No P0/P1 bugs open; tests green.

**Compliance**
- [ ] Eligible: Nigeria resident, adult, not affiliated with Perfect Corp or Devpost.
- [ ] Repo **public**, MIT licence, README with setup, all source and assets included.
- [ ] **No secrets in the repo or its history.** Key only in Render env.
- [ ] Video: 1–3 min (target 2:20), **public on YouTube**, names the YouCam API, shows the app working, no third-party trademarks or copyrighted music, English.
- [ ] Screenshots uploaded; text description explains features and consumer/eCommerce value.
- [ ] Testing link works without login, free, until **21 Nov**.
- [ ] Special-award opt-ins truthful (school email if Rising Star).
- [ ] All links open in an incognito window.
- [ ] **Submitted by Mon 2 Nov 14:00 WAT** (hard deadline 17:45 WAT). Status shows "Submitted".
- [ ] After submission: `main` frozen; credits monitored weekly until 21 Nov.

---
