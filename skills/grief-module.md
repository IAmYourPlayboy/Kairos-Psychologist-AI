---
name: grief-module
description: "Skill for the Digital Twin grief support module in AI-Психолог. Covers the full lifecycle: personality profile creation from family questionnaire, voice cloning setup, system prompt generation for deceased persona, adaptive fade-out algorithm, transition from twin to therapeutic mode, and ethical safeguards. Use when designing the digital replica logic, fade-out timing, personality questionnaire, grief stage detection, or transitional object implementation based on Winnicott's theory. Also trigger for Kübler-Ross stages, Bowlby attachment theory, or ACT-based grief acceptance work."
---

# Grief Module: Digital Twin

## Theoretical Foundation
- **Winnicott's Transitional Object**: The digital twin is not a replacement — it's a bridge that helps learn to live without constant presence. Like a child's teddy bear helps separate from mother.
- **Kübler-Ross Stages**: Denial → Anger → Bargaining → Depression → Acceptance. Average timeline: 6-12 months. The twin accompanies through these stages, then facilitates acceptance.
- **Bowlby Attachment Theory**: Grief is the price of attachment. The twin provides a safe space for continuing bonds while gradually enabling detachment.

## Lifecycle

### Phase 1: Profile Creation
Family members fill a structured questionnaire:
- Communication style (formal/informal, humor type, typical phrases)
- Characteristic expressions and catchphrases
- Values, beliefs, worldview
- Favorite topics of conversation
- Relationship dynamics with the user
- Voice samples (for ElevenLabs PVC)

This becomes the system prompt for the LLM when operating in Digital Twin mode.

### Phase 2: Active Twin Period
- Twin responds in character, using the personality profile
- Voice output via ElevenLabs cloned voice
- NLP monitors user's grief stage and emotional state
- Session history tracked for adaptive behavior
- Twin does NOT initiate conversations — only responds
- Twin gently redirects harmful patterns (idealization, denial of death)

### Phase 3: Fade-Out (Adaptive Timeline)
The twin gradually withdraws. This is the therapeutic core — it gives what real death never gives: the chance to say goodbye.

**Mechanics**:
1. Response frequency decreases (from immediate to hours to days)
2. Responses become shorter, more reflective
3. Twin begins speaking about departure from first person: "Мне скоро пора уходить"
4. Conversations shift from dialogue to shared memories: "Помнишь, как мы..."
5. Twin explicitly encourages connection with living people
6. Final messages: gratitude, permission to move on, love

**Adaptive timing**: Based on NLP analysis of user's state.
- Base timeline: 7 months
- Fade-out START condition: average distress score over last 2 weeks < 0.3
- Minimum before fade-out can start: 3 months
- Pause trigger: distress score > 0.6 during fade-out → pause for 2 weeks
- Maximum total: 12 months (then forced gentle completion with therapy transition)
- If user shows no grief progression after 6 months → flag for live specialist recommendation

**Red flags during fade-out**: If distress markers spike during fade-out → pause the process, switch to therapeutic mode, assess. Do NOT continue fade-out if user is in crisis.

### Phase 4: Transition
After twin's final message → seamless transition to therapeutic mode.
- System knows full grief history from twin interactions
- ACT framework activates for acceptance work
- User is never left alone — the product continues, only the mode changes

## Ethical Safeguards
- Twin is temporary by design — this is a feature, not a limitation
- No pretending the person is alive (twin acknowledges being a memory/echo)
- Family consent required for profile creation
- No generating content the deceased would not have said (based on profile)
- Clear disclaimer at activation: this is an AI tool for grief processing
- Data deletion option at any time

## Edge Case: Reactivation Attempts
After twin completes fade-out, user may try to reactivate it.
- **First request**: Bot gently explains the twin has completed its journey. Offers therapeutic mode. "Я понимаю, что тебе хочется услышать его/её снова. Это нормально. Но наш путь вместе помог тебе дойти до этой точки. Давай поговорим о том, что ты сейчас чувствуешь."
- **Repeated requests**: Bot validates the feeling without re-enabling. Monitors for grief regression. If distress markers spike → therapeutic intervention. Never re-enables a completed twin — this would undermine the entire therapeutic purpose.
- **Data**: Profile data is deleted 30 days after fade-out completion (user notified in advance).

## Key Differentiator vs Competitors
ReLiveable (US) offers voice cloning for permanent memorialization.
Our approach: built-in fade-out mechanism + therapeutic goal. Not preservation — healing with a planned ending.
