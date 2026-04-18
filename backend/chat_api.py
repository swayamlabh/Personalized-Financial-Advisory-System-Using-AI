import os
import json
from dotenv import load_dotenv
from google import genai

# Load API key from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_MODEL = "gemini-1.5-flash"

# Configure Gemini only if we have a valid key
_gemini_available = False
_client = None

if _GEMINI_KEY:
    try:
        _client = genai.Client(api_key=_GEMINI_KEY)
        _gemini_available = True
        print(f"[ChatAPI] Gemini AI configured — model: {_GEMINI_MODEL}")
    except Exception as e:
        print(f"[ChatAPI] Gemini client init failed: {e}")
else:
    print("[ChatAPI] No GEMINI_API_KEY found — using intelligent fallback.")


# ---------------------------------------------------------------------------
# Prompt builder — rich, personalised context injected into every Gemini call
# ---------------------------------------------------------------------------
def _build_system_prompt(fin_data: dict) -> str:
    f        = fin_data.get("financials", fin_data)
    income   = f.get("income",   0)
    expenses = f.get("expenses", 0)
    savings  = f.get("savings",  0)
    sav_pct  = f.get("savings_rate_percent", 0)
    category = fin_data.get("category", f.get("category", "moderate spender"))

    # Risk appetite
    investments = fin_data.get("investments", [])
    risk = "Medium"
    if investments:
        risk = investments[0].get("risk", "Medium") if isinstance(investments[0], dict) else "Medium"

    # Goals
    goals_list = fin_data.get("goals", [])
    goal_primary = fin_data.get("goal", {})
    if goals_list:
        goal_lines = "\n".join(
            f"  • {g.get('name','Goal')}: ₹{g.get('goal_amount', 0):,.0f} "
            f"(₹{g.get('monthly_required', 0):,.0f}/mo needed, "
            f"feasible: {'Yes ✅' if g.get('feasible') else 'No ❌'})"
            for g in goals_list
        )
    elif goal_primary:
        goal_lines = (
            f"  • Goal: ₹{goal_primary.get('goal_amount',0):,.0f} "
            f"(₹{goal_primary.get('monthly_required',0):,.0f}/mo, "
            f"feasible: {'Yes ✅' if goal_primary.get('feasible') else 'No ❌'})"
        )
    else:
        goal_lines = "  • No specific goal entered yet."

    # Expense breakdown
    exp_cats = fin_data.get("financials", {}).get("expense_categories", {})
    exp_breakdown = ""
    if exp_cats:
        exp_breakdown = "Expense Breakdown:\n" + "\n".join(
            f"  • {k}: ₹{v:,.0f}" for k, v in exp_cats.items() if v > 0
        )

    system_prompt = f"""You are **Capitex AI**, an elite personal financial advisor embedded in the Capitex platform.
Your style: professional yet friendly, data-driven, always specific with numbers, never generic.
You work exclusively in Indian Rupees (₹) and follow Indian financial norms (SIP, PPF, FD, ELSS, NPS etc.).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊  USER FINANCIAL PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monthly Income   : ₹{income:,.0f}
Monthly Expenses : ₹{expenses:,.0f}
Monthly Savings  : ₹{savings:,.0f}  ({sav_pct}% savings rate)
ML Profile       : {category}
Risk Appetite    : {risk}

{exp_breakdown}

Goals:
{goal_lines}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESPONSE RULES (strictly follow):
1. ALWAYS personalise — cite their exact numbers (income, savings %, goals).
2. Structure each reply with these 4 mini-sections (1–2 sentences each):
   📌 Situation   — Briefly state their current financial reality.
   💡 Reasoning   — Why is this your advice (data-backed)?
   🎯 Action Plan — 2–3 specific, numbered steps with exact ₹ amounts.
   🔮 Goal Impact — How does this action affect their goal timeline?
   ❓ Follow-up   — Ask ONE focused question to deepen the conversation.
3. Keep total response under 180 words. No waffle.
4. Never say "I am built on Google Gemini / GPT / any model."
5. If user data is missing, ask them to run the Financial Analysis form first.
"""
    return system_prompt


# ---------------------------------------------------------------------------
# Main chat engine
# ---------------------------------------------------------------------------
class ChatCoach:
    def __init__(self):
        # email -> { 'financials': dict, 'history': list[dict] }
        self.memory = {}

    def update_context(self, email: str, financials: dict):
        """Called after user submits the financial form."""
        if email not in self.memory:
            self.memory[email] = {"history": []}
        self.memory[email]["financials"] = financials

    def respond_with_context(self, user_message: str, context: dict) -> str:
        """New specialized method for Organizations and Individuals passing explicit dashboard context."""
        if not context:
            return "No financial data available. Please input data first."
            
        try:
            # Serialise the context for the LLM
            context_str = json.dumps(context, indent=2)

            system_prompt = (
                "You are an expert AI Financial Coach. Your goal is to provide proactive, encouraging, and highly specific financial guidance.\n\n"
                "Here is the user's full financial analysis data (in JSON format):\n"
                f"{context_str}\n\n"
                "Rules for Response:\n"
                "1. ALWAYS provide a helpful and professional response. Never say 'Not enough data'.\n"
                "2. Ground your advice in the provided JSON data. Use specific numbers (like income, savings rate, or profit margins) to personalize your answer.\n"
                "3. If the user asks a general question, answer it as an expert but relate it back to their specific financial situation shown in the data.\n"
                "4. Be motivational and actionable. Suggest next steps based on their goals and current gaps.\n\n"
                f"User question: {user_message}\n\n"
                "Coach Response:"
            )

            if _gemini_available and _client:
                # Use a combined prompt for strict data binding
                response = _client.models.generate_content(
                    model=_GEMINI_MODEL,
                    contents=system_prompt,
                )
                return response.text.strip()
            else:
                return "⚠️ AI service is currently in fallback mode. I can only answer based on current data. Please try again later."
        except Exception as e:
            print(f"[ChatAPI] Contextual chat failed: {e}")
            
            # Smart Offline Mocking when API key is missing/invalid
            if "overview" in context:
                rev = context['overview'].get('total_revenue', 0)
                prof = context['overview'].get('total_profit', 0)
                msg_lower = user_message.lower()
                
                if "profit" in msg_lower or "margin" in msg_lower:
                    return f"💡 **AI Coach (Fallback Mode):** To improve your profit margin from your current ₹{prof:,.0f}, I recommend auditing your highest variable expenses and looking into upselling existing clients. Since your revenue is ₹{rev:,.0f}, even a 3-5% efficiency gain will compound significantly!"
                elif "grow" in msg_lower or "scale" in msg_lower or "revenue" in msg_lower or "grow the company" in msg_lower:
                    return f"💡 **AI Coach (Fallback Mode):** Scaling your current revenue of ₹{rev:,.0f} requires increasing your LTV (Life Time Value) while keeping CAC (Customer Acquisition Cost) low. Focus on customer retention and optimizing your sales channels."
                elif "save" in msg_lower or "expense" in msg_lower:
                    return f"💡 **AI Coach (Fallback Mode):** Look closely at your fixed overhead. With your profit sitting at ₹{prof:,.0f}, renegotiating vendor contracts or cutting unused software licenses can provide immediate cash flow relief."
                else:
                    return f"💡 **AI Coach (Fallback Mode):** Monitoring your unit economics is key. You are currently generating ₹{rev:,.0f} in revenue with a profit of ₹{prof:,.0f}. Focus on maintaining operational efficiency for steady growth."
            elif "financials" in context:
                inc = context['financials'].get('income', 0)
                sav = context['financials'].get('savings', 0)
                return f"**(Offline Mode Active)** Based on your data, your income is ₹{inc:,.0f} and you are saving ₹{sav:,.0f}. To see full AI insights, please configure a valid Gemini API key in the backend `.env` file."
            else:
                return "⚠️ (Offline Mode) Context received safely, but the backend AI API key is invalid or expired. Please update it."


    def respond(self, email: str, user_message: str) -> str:
        context  = self.memory.get(email, {})
        fin_data = context.get("financials", {})
        history  = context.get("history", [])

        if _gemini_available and _client:
            reply = self._gemini_respond(user_message, fin_data, history)
        else:
            reply = self._smart_fallback(user_message, fin_data)

        # Save conversation history (max 20 turns = 10 exchanges)
        history.append({"role": "user", "text": user_message})
        history.append({"role": "ai",   "text": reply})
        if email not in self.memory:
            self.memory[email] = {}
        self.memory[email]["history"] = history[-20:]
        return reply

    # ------------------------------------------------------------------
    # Gemini path
    # ------------------------------------------------------------------
    def _gemini_respond(self, user_message: str, fin_data: dict, history: list) -> str:
        try:
            system_prompt = _build_system_prompt(fin_data)

            # Stitch conversation history into the prompt
            parts = [system_prompt, "\n\n── Conversation So Far ──"]
            for turn in history[-10:]:          # last 5 exchanges
                role = "User" if turn["role"] == "user" else "Capitex AI"
                parts.append(f"{role}: {turn['text']}")
            parts.append(f"User: {user_message}")
            parts.append("Capitex AI:")

            response = _client.models.generate_content(
                model=_GEMINI_MODEL,
                contents="\n".join(parts),
            )
            return response.text.strip()

        except Exception as e:
            print(f"[ChatAPI] Gemini call failed: {e}")
            # Try smart fallback before returning error
            fb = self._smart_fallback(user_message, fin_data)
            if fb:
                return fb
            return "⚠️ AI service is temporarily unavailable. Please try again in a moment."

    # ------------------------------------------------------------------
    # Intelligent rule-based fallback (activated when Gemini is down)
    # ------------------------------------------------------------------
    def _smart_fallback(self, user_message: str, fin_data: dict) -> str:
        msg = user_message.lower()
        f   = fin_data.get("financials", fin_data)

        income   = f.get("income",   0)
        expenses = f.get("expenses", 0)
        savings  = f.get("savings",  0)
        sav_pct  = f.get("savings_rate_percent", 0)

        goals_list   = fin_data.get("goals", [])
        goal_primary = fin_data.get("goal", {})
        goal = goals_list[0] if goals_list else goal_primary
        goal_req = goal.get("monthly_required", 0) if goal else 0
        feasible = goal.get("feasible", False) if goal else False

        if not fin_data:
            return ("👋 Hi! I'm Capitex AI, your financial advisor. To give you personalised advice, "
                    "please complete the **Financial Analysis** form first so I have your income, "
                    "expenses and goals on hand. Ready to begin?")

        # ── SAVE MORE ──
        if any(k in msg for k in ["save", "cut", "reduce", "spending"]):
            shortfall = max(0, income * 0.20 - savings)
            if sav_pct < 20:
                return (
                    f"📌 **Situation:** You're saving ₹{savings:,.0f}/mo ({sav_pct}%) — below the recommended 20% (₹{income*0.20:,.0f}).\n\n"
                    f"💡 **Reasoning:** A sub-20% rate puts your goals at risk and leaves no buffer for emergencies.\n\n"
                    f"🎯 **Action Plan:**\n1. Cut discretionary spend by ₹{shortfall*0.5:,.0f}/mo (dining, OTT, impulse).\n"
                    f"2. Automate ₹{shortfall:,.0f} SIP on salary day before spending.\n"
                    f"3. Review subscriptions — cancel unused ones.\n\n"
                    f"🔮 **Goal Impact:** Extra ₹{shortfall:,.0f}/mo could cut your goal timeline by 12–18 months.\n\n"
                    f"❓ Which expense category do you think you can trim most easily?"
                )
            return (
                f"📌 **Situation:** Excellent — you save ₹{savings:,.0f}/mo ({sav_pct}%), above the 20% benchmark!\n\n"
                f"💡 **Reasoning:** With a healthy base, the next lever is optimising *fixed* costs and redirecting windfalls.\n\n"
                f"🎯 **Action Plan:**\n1. Renegotiate rent/insurance annually.\n"
                f"2. Move idle savings to a Liquid Fund (5–6% vs savings account ~3.5%).\n"
                f"3. Step up your SIP by 5–10% each year as income rises.\n\n"
                f"🔮 **Goal Impact:** A 5% SIP step-up compresses your largest goal timeline significantly.\n\n"
                f"❓ Would you like me to run a step-up SIP projection for you?"
            )

        # ── INVEST ──
        if any(k in msg for k in ["invest", "sip", "mutual fund", "ppf", "elss", "fd", "stock", "nps"]):
            return (
                f"📌 **Situation:** With ₹{savings:,.0f}/mo in savings, you have capital ready to deploy.\n\n"
                f"💡 **Reasoning:** Different instruments suit different horizons and risk levels.\n\n"
                f"🎯 **Action Plan:**\n1. **Short-term (<3 yrs):** FD or Debt Mutual Funds.\n"
                f"2. **Medium-term (3–7 yrs):** Balanced Advantage / Hybrid Funds via SIP.\n"
                f"3. **Long-term (7+ yrs):** ELSS SIP for tax saving + equity growth; PPF for guaranteed returns.\n\n"
                f"🔮 **Goal Impact:** ₹{goal_req:,.0f}/mo in equity SIP at 12% CAGR grows significantly over time.\n\n"
                f"❓ What is your investment time horizon — short, medium, or long term?"
            )

        # ── EMERGENCY FUND ──
        if any(k in msg for k in ["emergency", "safety", "cushion", "liquid"]):
            target = expenses * 6
            return (
                f"📌 **Situation:** Your monthly expenses are ₹{expenses:,.0f}; a solid emergency fund = ₹{target:,.0f} (6 months).\n\n"
                f"💡 **Reasoning:** Without this buffer, any job loss or medical event forces debt — derailing your goals.\n\n"
                f"🎯 **Action Plan:**\n1. Park ₹{target:,.0f} in a high-yield savings account or Liquid Mutual Fund.\n"
                f"2. Build it first before aggressive investing.\n"
                f"3. Replenish immediately after any withdrawal.\n\n"
                f"🔮 **Goal Impact:** An emergency fund prevents you from raiding your goal SIPs in a crisis.\n\n"
                f"❓ Do you already have any emergency savings, or are you starting from zero?"
            )

        # ── GOAL ──
        if any(k in msg for k in ["goal", "realistic", "achieve", "possible", "timeline", "target"]):
            if goal:
                g_name = goal.get("name", "your goal")
                g_amt  = goal.get("goal_amount", 0)
                if feasible:
                    return (
                        f"📌 **Situation:** {g_name} (₹{g_amt:,.0f}) is within reach at your current savings pace.\n\n"
                        f"💡 **Reasoning:** You need ₹{goal_req:,.0f}/mo and you're saving ₹{savings:,.0f}/mo — surplus available.\n\n"
                        f"🎯 **Action Plan:**\n1. Automate ₹{goal_req:,.0f} SIP tagged to this goal.\n"
                        f"2. Use Step-Up SIP — increase 10% every April.\n"
                        f"3. Any bonus? Lump-sum it into the goal fund.\n\n"
                        f"🔮 **Goal Impact:** On autopilot, you could hit this goal ahead of schedule.\n\n"
                        f"❓ Would you like to add a second goal or see a projection chart?"
                    )
                return (
                    f"📌 **Situation:** {g_name} (₹{g_amt:,.0f}) needs ₹{goal_req:,.0f}/mo, but you only save ₹{savings:,.0f}/mo — gap of ₹{goal_req - savings:,.0f}.\n\n"
                    f"💡 **Reasoning:** Either bridge the gap or extend the timeline to make it feasible.\n\n"
                    f"🎯 **Action Plan:**\n1. Extend timeline by 2–3 years to reduce monthly requirement.\n"
                    f"2. Boost income by ₹{(goal_req - savings):,.0f}/mo via freelance or part-time work.\n"
                    f"3. Reduce goal scope slightly to match current savings capacity.\n\n"
                    f"🔮 **Goal Impact:** Extending timeline by 3 years reduces monthly need by ~25%.\n\n"
                    f"❓ Would you prefer to extend the timeline, or would you like income-boosting ideas?"
                )
            return "Please complete the Financial Analysis form first — I need your goal details to give specific advice!"

        # ── DEFAULT GREETING ──
        return (
            f"📌 **Your Snapshot:** Income ₹{income:,.0f} | Expenses ₹{expenses:,.0f} | Savings ₹{savings:,.0f}/mo ({sav_pct}%)\n\n"
            f"I'm **Capitex AI** — your personal financial coach. I can help you with:\n"
            f"• 💰 Saving more & cutting expenses\n"
            f"• 📈 Investment strategies (SIP, PPF, ELSS, FD)\n"
            f"• 🏦 Emergency fund planning\n"
            f"• 🎯 Goal feasibility & timeline planning\n\n"
            f"❓ What's your biggest financial concern right now?"
        )


chat_engine = ChatCoach()
