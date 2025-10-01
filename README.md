# Haikyu_sim

This is a project for simulating parameters for game design

----

here is the initial design rules for the game and for the simulator to be built:

# 🏐 Volleyball Card Game — Simulator Specification & Full Rules (v1)

This document contains everything needed to **implement a simulator** for the Volleyball Card Game, plus the **current rules and design goals** to validate via simulation.

---

## 0) Design Goals (What the simulator should help validate)

1. **Rally feel** — Are rallies too short/long?  
   - Target: **5–9 card plays per rally** on average.

2. **Block impact** — Exact-match blocks should be rare but meaningful.  
   - Target: **8–18%** of attacks face a block attempt; **3–10%** actually succeed.

3. **2-touch utility** — The ±2 weakened attack should make 2-touch situational, not dominant.  
   - Target: Used in **10–30%** of rallies; rallies that used 2-touch should have win rate within **±5%** of baseline.

4. **Server advantage** — Serving should be a modest edge.  
   - Target: **50–58%** server point win rate.

5. **Hand pressure** — Hands shouldn’t be so tight that rallies mostly end by exhaustion.  
   - Target: **< 20%** of points end from “no valid play”.

6. **Set length pacing** — Total rallies to reach 10 or 25 points should feel brisk.  
   - Target: 10-point set ≈ **10–16 rallies**, 25-point set ≈ **25–45 rallies** (variance expected).

7. **Balance of specials/characters (later)** — No single special or character should raise win% by **> 7 percentage points** over average across many seeds.

---

## 1) Game Rules (Current Canon)

### 1.1 Components
- **Deck (65 cards)**  
  - 4 standard suits (♠, ♥, ♦, ♣) with values **1–13**.  
  - 1 special suit (★) “Technique Cards” (13 unique effects) — **off in baseline simulation** (V1+ only).

- **Players & Modes**  
  - Ideal: **3 vs 3** (6 players). Also supports **2 vs 2**, **1 vs 1**, **1 vs 2**, **2 vs 3**.

- **Hand size**  
  - Default **5** cards per player (base rules). Asymmetry modifies this (see §1.6).

### 1.2 Roles & Formation
- Before each rally, teams secretly assign roles: **Serve, Reception, Pass, Attack/Block**.  
- Roles rotate each rally; some characters grant role-based bonuses (V2+).

### 1.3 Rally Sequence (Core Flow)
1. **Serve:** Server plays any card face up.  
2. **Receiving Team** must play (in order):  
   - **Reception:** play **higher** than serve.  
   - **Pass:** play **lower** than Reception.  
   - **Attack:** play **lower** than Pass (unless a special effect/feint overrides).  
3. **Serving Team** then responds:  
   - **Reception:** play **lower** than opponent Attack.  
   - **Pass:** play **higher** than that Reception.  
   - **Attack:** play **higher** than that Pass.  
4. Alternate sequences until a side **cannot play a valid card** → other side wins the rally/point.

### 1.4 Blocks
- **Exact match** vs the **Attack** value on the **defending Reception** = **Block** (base rule).  
- **Effect:** attacker’s card is spent; **blocker keeps** their card; ball bounces back (momentum reversal).  
- **Extensions (V2/V1):** characters or ★ cards may widen block window to ±1 or more.

### 1.5 Feints
- **Feint** = Attacker plays a card in the “wrong direction” (e.g., higher instead of lower) yet it still counts as an Attack.  
- Blocks can be baited and wasted; some characters/★ amplify feints.  
- **Baseline simulator:** turn **OFF** feints initially to keep the model clean; add later as a toggle.

### 1.6 Two-Touch Return (Universal Rule)
A team may return the ball after only **two touches** instead of three.
- The final card counts as **Attack** even if it was a Reception/Pass.  
- **Weakened attack:** Opponent’s Reception is checked against **Attack ± 2** (i.e., it’s **2 easier** to receive).  
  - Example: Attack = 6 → opponent only needs to play **lower than 8** instead of lower than 6.  
- **Discard penalty:** In base rules, any player who skipped their role discards 1 card **after the rally**.  
- **Asymmetric exception:** In **1v2** or **2v3**, the short-handed team may perform **one 2-touch per rally without the discard penalty** (the ±2 weakening still applies).

### 1.7 Hand & Stamina Model
- “Stamina” = **cards in hand**.  
- After each rally, draw back up to your hand size.  
- Optional house rule: before drawing, **discard 1** (to cycle) — **off in baseline**.

### 1.8 Special Suit (★) — Overview (V1+)
- 13 cards with effects (e.g., ★A Diving Save, ★4 One-Touch Block, ★8 Quick Set, ★K Momentum Shift).  
- **Baseline simulation V0:** ★ effects disabled. Add progressively in V1+.

### 1.9 Characters — Overview (V2+)
- Role-based bonuses (e.g., Hinata ±2 Attack, Kageyama draw-on-Pass, Tsukishima ±1 Block).  
- Start with a minimal roster in V2+ experiments.

### 1.10 Scoring
- Rally scoring (like volleyball). First to **25** (or **10** for quick tests) wins the set. Best-of series optional.

---

## 2) Simulation Scope & Phases

### V0 — Baseline (Recommended to implement first)
- **No specials, no characters, no feints.**  
- Teams represented as **pooled hands**: start as 15 cards per team (3×5 abstraction).  
- Core constraints: up/down flow, **exact-match blocks**, **2-touch ±2**.  
- Discard penalty for 2-touch: **OFF** (toggleable).

### V1 — Specials
- Add ★ suit to deck; enable effects via toggles per card ID (start with a small subset).

### V2 — Characters & Seats
- Split team hands into 3 “seats” (Reception/Pass/Attack) with per-seat hand sizes and powers.  
- Implement a small roster (Karasuno vs Karasuno, then vs Rivals).

### V3 — Asymmetric Modes
- **1v1:** 7-card hands each; may 2-touch once per rally without penalty.  
- **1v2:** Solo 7 vs 5+5; solo may 2-touch once per rally without penalty; may merge Pass+Attack at rally start.  
- **2v3:** Short team 6+6 vs 5×3; short team may 2-touch once per rally without penalty; free role exchange at rally start.

---

## 3) Bot Policies (Pluggable Strategies)

### 3.1 Reception Policy (higher/lower checks)
- **Greedy-low valid** (default): play the **lowest** valid card satisfying the constraint.  
- **Greedy-high valid:** play the **highest** valid.  
- **Heuristic (later):** keep pivot values (6–8) to preserve future options.

### 3.2 Pass Policy
- **Greedy-low valid** plus a safeguard: avoid leaving **no lower** for Attack (track existence of at least one valid Attack card).

### 3.3 Attack Policy
- **Greedy-low valid** (default).  
- **Pressure mode:** prefer ≤4 if valid (harder to receive), else lowest valid.

### 3.4 2-Touch Decision
- Use 2-touch if:  
  - No valid Pass (or no valid Attack after the Pass forecast), **or**  
  - Estimated continuation chance < threshold (e.g., <30%), **or**  
  - Low-probability tempo gambit (e.g., 5–10% random).

### 3.5 Block Attempt
- Attempt block if **exact-match** card exists in defending Reception slot.  
- V2+: widen window per character (e.g., ±1).

### 3.6 Specials/Feints (V1+)
- Initially: deterministic triggers (if condition satisfied, play).  
- Later: evaluate EV vs keeping the card.

---

## 4) Data Structures

```text
Card:
  value: int (1..13)
  suit: enum {SPADE, HEART, DIAMOND, CLUB, STAR}
  is_special: bool
  special_id: Optional[str]  # e.g., "STAR_A", "STAR_4"

Team:
  hand: multiset/list[Card]           # V0 pooled; V2 split across seats
  policy: PolicyConfig
  specials_enabled: bool
  characters: Optional[List[Character]]  # V2+
  seat_hands: Optional[dict]         # {"RECV": [...], "PASS": [...], "ATK": [...]}

PolicyConfig:
  reception_mode: {"low", "high", "heuristic"}
  pass_mode: {"low", "low_safe"}
  attack_mode: {"low", "pressure"}
  two_touch_mode: {"threshold", "random", "never", "always_test"}
  block_window: int  # 0 for exact, 1 for ±1 (V2)

RallyState:
  last_card: Optional[Card]
  phase: enum {SERVE, R_SEQ, S_SEQ}
  step_in_sequence: enum {RECV, PASS, ATK}
  can_two_touch: bool
  two_touch_used_this_rally: bool
  history: list[CardPlay]
```

---

## 5) Core Algorithms (Pseudocode)

### 5.1 Setup & Dealing
```
build_deck(include_specials: bool) -> List[Card]
shuffle(deck)
deal(teamA, teamB, hand_sizes)  # pooled or per-seat depending on version
set server = random choice (A/B)
```

### 5.2 Rally Loop
```
function play_rally(state, server_team):
  active = server_team
  inactive = other(server_team)

  # Serve
  serve_card = active.policy.choose_serve(active.hand)
  play(serve_card)

  # Alternate sequences:
  while True:
    # Receiving team sequence: HIGH -> LOW -> LOW
    if not sequence_turn(inactive, constraints=[HIGH, LOW, LOW]):
        return POINT to active
    # Serving team sequence: LOW -> HIGH -> HIGH
    if not sequence_turn(active, constraints=[LOW, HIGH, HIGH]):
        return POINT to inactive
```

### 5.3 Sequence Turn
```
function sequence_turn(team, constraints):
  for each constraint step with label in [RECV, PASS, ATK]:
     # Optional: 2-touch decision at PASS step (or RECV step) per policy
     if can_two_touch(team, step) and team.policy.use_two_touch(state):
         # play the current step as final Attack
         atk_card = choose_card_for_attack(team.hand, constraint_for_step(step))
         apply_two_touch_penalty_to_next_reception(atk_card)  # ±2
         record_two_touch()
         return True  # control passes to opponent after one step left unused

     # Normal play
     card = choose_card(team.hand, constraint, state)
     if not card: return False  # cannot continue
     # If ATK just played, check for Block on opponent reception window
     set_state(card)
  return True
```

### 5.4 Constraints
- `HIGH`: choose minimal card **> target**  
- `LOW`: choose minimal card **< target**  
- Two-touch sets a flag so that the opponent’s **next Reception** compares to **(Attack ± 2)** instead of Attack.

### 5.5 Block Check
- When opponent will perform **Reception** vs your **Attack**:  
  - If they have a card **== Attack** (or within block_window), they may **Block**.  
  - On block: attacker card remains spent; defender keeps their block card; **return control** to attacker’s side immediately.  
  - Pseudocode: during defending Reception choice, check block option first.

### 5.6 End of Rally
- Winner gets point.  
- Both teams **draw back up to hand size** (pooled or per seat).  
- Rotate server; reset flags.

---

## 6) Metrics & Logging

Per rally log:
- `rally_id`, `server_side`
- `cards_played_count`
- `block_attempted`, `block_success`
- `two_touch_used_by` (A/B/None), `two_touch_success` (rally won?), `two_touch_step` (after RECV or after PASS)
- `end_reason` ∈ {NO_RECV, NO_PASS, NO_ATTACK, DECK_EXHAUST, CAP_RALLY_LIMIT}
- `start_hand_sizes`, `end_hand_sizes`
- `reshuffles`

Aggregates:
- Average/median rally length; histogram
- Server win rate; sideout rate
- Block attempt & success rates
- 2-touch usage & win differential
- Exhaustion-ended %
- Set length distribution (rallies to 10/25 points)

---

## 7) Experiment Matrix

**A. Baseline sensitivity (V0):**
1. Hand size: 5 vs 6.  
2. Block window: 0 (exact) vs 1 (feel test).  
3. 2-touch penalty: ±1 vs **±2 (final)** vs previous-card rule (for comparison).  
4. Attack policy: lowest valid vs pressure (prefer ≤4).

**B. Specials (V1):**
- Toggle on ★A Diving Save, ★4 One-Touch Block, ★8 Quick Set first; measure changes.  
- Then layer more; watch for win% spikes.

**C. Characters (V2):**
- Karasuno mirror, then vs Rivals.  
- Flag any character that pushes win rate over ~57–60% across many seeds.

**D. Asymmetry (V3):**
- 1v2 and 2v3 using (+2 cards for short team, free 2-touch once per rally).  
- Aim short-team overall win rate ~40–50% depending on policies; adjust hand bonus if needed.

---

## 8) Edge Cases & Safeguards
- **No valid Reception on serve** → immediate point; track frequency (if high, consider serve ≤10 cap).  
- **Loop prevention**: set a **rally cap** (e.g., 40 plays). If hit, award side-out to the non-active team.  
- **Deck exhaustion**: reshuffle discards into new deck; count reshuffles.  
- **Identical hands stalemate**: add small tiebreak rule (e.g., force 2-touch attempt if 3 consecutive passes create no progress).

---

## 9) Implementation Notes

- **Language:** Python recommended.  
- **Randomness:** seed RNG per run for reproducibility.  
- **Performance:** Avoid heavy per-play logging; aggregate after each rally.  
- **Config file:** JSON/YAML with keys like:
```json
{
  "include_specials": false,
  "include_characters": false,
  "hand_size": 5,
  "block_window": 0,
  "two_touch_penalty": 2,
  "two_touch_penalty_enabled": true,
  "free_two_touch_short_team": true,
  "feints_enabled": false,
  "serve_advantage_tweaks": null,
  "rally_cap": 40,
  "num_games": 500,
  "points_to_win": 25
}
```
- **Output:** Summaries to console + CSV (per rally and per game), optional charts later.

---

## 10) Roadmap Summary

1. **V0 Baseline** — pooled hands; exact blocks; 2-touch ±2; no specials/characters/feints.  
2. **V1 Specials** — enable ★ with toggles; measure deltas.  
3. **V2 Characters** — seat-based hands & powers; start with a small roster.  
4. **V3 Asymmetry** — 1v1, 1v2, 2v3 per rules above; validate fairness.

---

## 11) Appendix — Current Special ★ Cards (for V1 reference)

- **★A (Diving Save)** – Reception valid vs any value.  
- **★2 (Rolling Thunder)** – After play, draw 1.  
- **★3 (Decoy)** – Attack may be higher instead of lower.  
- **★4 (One-Touch Block)** – Block window widens to ±1.  
- **★5 (Back Attack)** – Attack immediately after Pass (skip reception).  
- **★6 (Soft Touch)** – Opponent’s next Reception must be lower instead of higher.  
- **★7 (Perfect Receive)** – Counts as any number 4–10.  
- **★8 (Quick Set)** – Swap Pass and Attack this rally.  
- **★9 (Feint Mastery)** – Opponent’s next Pass must be lower instead of higher.  
- **★10 (Power Spike)** – If not blocked, opponent discards 1.  
- **★J (Tandem Attack)** – Two teammates each play 1 Attack; keep best.  
- **★Q (Libero Save)** – Recover one just-discarded card.  
- **★K (Momentum Shift)** – Reverse up/down sequences for both teams.

---

With this spec, you can implement the simulator incrementally, capture the right metrics, and quickly spot which rules feel great and which need tuning.
