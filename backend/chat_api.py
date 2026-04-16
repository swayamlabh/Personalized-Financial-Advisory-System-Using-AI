import re
import math

class ChatCoach:
    def __init__(self):
        # We store conversation memory by user email to maintain context.
        # Structure: email -> { 'financials': dict, 'history': list }
        self.memory = {}

    def update_context(self, email, financials):
        """Called when user submits the financial form"""
        if email not in self.memory:
            self.memory[email] = {'history': []}
        self.memory[email]['financials'] = financials

    def respond(self, email, user_message):
        context = self.memory.get(email, {})
        fin_data = context.get('financials', {})
        msg = user_message.lower()
        
        reply = "I'm your AI Financial Coach. Could you clarify your question?"
        
        # simulated intents
        if "save more" in msg or "cut expense" in msg:
            if fin_data:
                savings_pct = fin_data.get('savings_rate_percent', 0)
                if savings_pct < 20:
                    reply = f"Since your saving rate is {savings_pct}%, which is below the recommended 20%, I suggest analyzing your 'Wants' category. Cutting discretionary spending like dining out or subscriptions by just 10% could significantly boost your safety net."
                else:
                    reply = f"You are doing well at {savings_pct}%! To save even more, look at fixed expenses—can you optimize utility bills, or switch to a cheaper subscription model? Any extra savings should go directly into your investment SIP to compound faster."
            else:
                reply = "To tell you how to save more, please run the Analysis from the input dashboard first!"
                
        elif "goal" in msg and ("realistic" in msg or "achievable" in msg or "possible" in msg):
            if fin_data:
                goal_data = fin_data.get('goal', {})
                if goal_data.get('feasible'):
                    reply = f"Yes! Based on your {fin_data.get('savings')} monthly savings, setting aside {goal_data.get('monthly_required',0):.0f} for your goal is perfectly realistic."
                else:
                    reply = f"Currently, no. Your goal requires {goal_data.get('monthly_required',0):.0f}/month, but you only save {fin_data.get('savings',0):.0f}. I recommend extending the timeline by a few years or reducing the goal amount temporarily."
            else:
                reply = "I need your financial data first to analyze your goal!"
                
        elif "invest" in msg or "return" in msg or "sip" in msg:
            reply = "For investing, I always recommend aligning with your risk appetite. For high growth (over 7+ years), Equity Mutual Funds (SIPs) are best. For stability, mix in some Fixed Deposits."
            
        elif "emergency" in msg or "fund" in msg:
            if fin_data:
                exp = fin_data.get('expenses', 0)
                target = exp * 6
                reply = f"Your monthly expenses are {exp}. A solid emergency fund (6 months) should be around {target:,.0f}. Make sure this is stored in a highly liquid asset like a high-yield savings account or liquid mutual fund before chasing risky investments."
            else:
                reply = "An emergency fund should cover 3-6 months of your expenses."
        else:
            reply = "I'm analyzing your profile context... As your AI coach, I recommend focusing on consistent monthly investments. Ask me how to save more or if your goal is realistic!"
            
        # Append to history
        if 'history' in context:
            context['history'].append({"user": user_message, "ai": reply})
            
        return reply

chat_engine = ChatCoach()
