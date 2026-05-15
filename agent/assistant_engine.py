#Python feature that changes how type hints are handled.
#such as :    def to_dict(self) -> dict[str, Any] ,it mean the function to_dict will return a dictionary where the keys are strings and the values can be of any type.
#for this to work we need to import annotations from __future__ which allows us to use the new type hinting syntax that was introduced in Python 3.9, even if we're running an older version of Python.
from __future__ import annotations

import re #regular expressions for pattern matching in strings
from dataclasses import dataclass # creating cleaner data classes automatically @dataclass
from typing import Any #datatypes that can be used for type hints

#-------------------------------------The BbooAssistantEngine class is designed
'''
a decorator → @dataclass
an optimization option → slots=True
---
Python automatically creates: __init__, __repr__, __eq__, 
and other special methods for the class based on the defined fields.
look the example below:
'''
@dataclass(slots=True)
class RetrievalNote:

    '''def __init__(self, title, content, score):
        self.title = title        title: str
        self.content = content    content: str
        self.score = score        score: int
        XXXxx becuse you use @dataclass'''
    title: str
    content: str
    score: int
#Returns dictionary its key are string and value can be any type
#-> is a **type hint** indicating the return type of the function
    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "content": self.content, "score": self.score}

#------------------------------------------------------
@dataclass(slots=True)
class AgentResponse:
    reply: str
    intent: str
    tool_name: str | None = None
    tool_status: str = "none"
    action_payload: dict[str, Any] | None = None
    retrieved_notes: list[RetrievalNote] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "reply": self.reply,
            "intent": self.intent,
            "tool_name": self.tool_name,
            "tool_status": self.tool_status,
            "action_payload": self.action_payload or {},
            "retrieved_notes": [note.to_dict() for note in (self.retrieved_notes or [])],
        }


class BbooAssistantEngine:
    def __init__(self) -> None:
        #knowledge base is a list of dictionaries,
        #where each dictionary represents a piece of knowledge with a title, content, and associated keywords.
        #The keywords are stored as a set for efficient lookup during retrieval.
        self.knowledge_base = [
            {
                "title": "Session tuning",
                "content": "Shorter focus sessions are best when energy is low. Longer sessions work better after consistent sleep and fewer distraction hours.",
                "keywords": {"session", "minutes", "focus", "timer", "study"},
            },
            {
                "title": "Sleep protection",
                "content": "Protect bedtime by reducing scrolling during the two hours before sleep. A stable bedtime helps focus scores recover faster.",
                "keywords": {"sleep", "bedtime", "night", "protect", "hours"},
            },
            {
                "title": "Weekly recovery",
                "content": "Weekly progress is strongest when check-ins, timer completions, and app usage updates are recorded consistently across the week.",
                "keywords": {"week", "weekly", "summary", "progress", "improve", "streak"},
            },
            {
                "title": "Risk window coaching",
                "content": "Your risk window is the time of day where distraction tends to rise. Use lighter tasks or shorter timers during that window.",
                "keywords": {"risk", "window", "distract", "distraction", "evening"},
            },
            {
                "title": "App usage coaching",
                "content": "Tracking app usage for seven days reveals which apps consume the most time and whether that pressure is increasing or stabilizing.",
                "keywords": {"app", "usage", "hours", "history", "seven", "7"},
            },
        ]
    #handle_message is the main function that processes incoming messages, updates settings, starts timers, and retrieves summaries based on user input.
    def handle_message(self, *, message: str, session: dict[str, Any], repository, dashboard: dict[str, Any], settings: dict[str, Any]) -> AgentResponse:
        text = message.strip()
        lowered = text.lower()

        if not text:
            return AgentResponse(
                reply="Please type a request like 'change my session time to 45 minutes' or 'show my weekly summary.'",
                intent="empty",
            )
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#in this class global note 
    # 💥note in the wepsite:Application settings in profile page

            #💥note:repository.update_settings it in 
            # -> storage/mysql_repository.py that called in the app.py _handle_update_settings() file and in api_fastapi.py update_settings() function
            # -> MySQLRepository(MySQLConfig()):::: updating using user_id
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Update Session Time----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #V this regular expression looks for phrases that indicate the user wants to update their focus session time, such as "session time 45" or "focus minutes 30".
        #  It captures the number of minutes specified by the user.
        update_session = re.search(r"(?:session|focus)\s+(?:time|minutes?)\D{0,10}(\d{2,3})", lowered)
        if update_session:
            minutes = int(update_session.group(1))
            if not 10 <= minutes <= 120:
                raise ValueError("Session time must stay between 10 and 120 minutes.")
            
            #-glabal note in this calss
            updated_settings = repository.update_settings(
                session["user_id"],
                {
                    **settings,
                    "default_session_minutes": minutes,
                },
            )
            return AgentResponse(
                reply=f"Your default focus session is now {minutes} minutes.",
                intent="update_setting",
                tool_name="update_session_minutes",
                tool_status="success",
                action_payload={"settings": updated_settings},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Rename Application Name----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 💥note in the wepsite:Application settings in profile page
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        rename_match = re.search(r"(?:rename|change)\s+(?:the\s+)?app(?:lication)?\s+name\s+(?:to\s+)?(.+)", text, re.IGNORECASE)
        if rename_match:
            app_name = rename_match.group(1).strip().strip(".")
            if not app_name:
                raise ValueError("Please provide the new application name.")
            
            #-glabal note in this calss
            updated_settings = repository.update_settings(
                session["user_id"],
                {
                    **settings,
                    "app_name": app_name[:120],
                },
            )
            return AgentResponse(
                reply=f"The application name is now {updated_settings['app_name']}.",
                intent="update_setting",
                tool_name="update_app_name",
                tool_status="success",
                action_payload={"settings": updated_settings},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #change bedtime ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 💥note in the wepsite:Application settings in profile page
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        bedtime_match = re.search(r"(?:bedtime|sleep protection time|sleep time).{0,16}?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lowered)
        if bedtime_match and any(token in lowered for token in ("bedtime", "sleep")):
            hour = int(bedtime_match.group(1))
            minute = int(bedtime_match.group(2) or 0)
            meridiem = bedtime_match.group(3)
            if meridiem == "pm" and hour < 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
            if hour > 23 or minute > 59:
                raise ValueError("Please use a real time for bedtime, like 22:30 or 10:30 PM.")
            bedtime_target = f"{hour:02d}:{minute:02d}"
            #-glabal note in this calss
            updated_settings = repository.update_settings(
                session["user_id"],
                {
                    **settings,
                    "bedtime_target": bedtime_target,
                },
            )
            return AgentResponse(
                reply=f"Your bedtime target is now {bedtime_target}.",
                intent="update_setting",
                tool_name="update_bedtime_target",
                tool_status="success",
                action_payload={"settings": updated_settings},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #change sleep target hours----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 💥note in the wepsite:Application settings in profile page
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        sleep_target_match = re.search(r"sleep\s+(?:target|goal|hours?).{0,12}?(\d{1,2})", lowered)
        if sleep_target_match:
            hours = int(sleep_target_match.group(1))
            if not 4 <= hours <= 12:
                raise ValueError("Sleep target hours should stay between 4 and 12.")
            updated_settings = repository.update_settings(
                session["user_id"],
                {
                    **settings,
                    "sleep_target_hours": hours,
                },
            )
            return AgentResponse(
                reply=f"Your sleep target is now {hours} hours.",
                intent="update_setting",
                tool_name="update_sleep_target_hours",
                tool_status="success",
                action_payload={"settings": updated_settings},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #start focus timer----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 💥note in the wepsite:Application settings in profile page
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        timer_match = re.search(r"(?:start|begin)\s+(?:a\s+)?(?:focus\s+)?timer(?:\s+for)?\D{0,10}(\d{2,3})", lowered)
        if timer_match:
            minutes = int(timer_match.group(1))
            if not 10 <= minutes <= 180:
                raise ValueError("Timer length must stay between 10 and 180 minutes.")
            label = "Agent-started focus timer"
            repository.start_focus_timer(session["user_id"], minutes, label)
            timers = repository.recent_timers(session["user_id"])
            return AgentResponse(
                reply=f"I started a {minutes}-minute focus timer for you.",
                intent="timer_action",
                tool_name="start_focus_timer",
                tool_status="success",
                action_payload={"timers": timers},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #weekly summary----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 💥Retrieved weekly summary information for the user
        #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #for the weekly summary question 
        if any(phrase in lowered for phrase in ("weekly summary", "weekly progress", "how did i do this week", "show my progress")):
            summary = repository.weekly_summary(session["user_id"])
            return AgentResponse(
                reply=(
                    f"{summary['headline']} You completed {summary['completed_sessions_this_week']} sessions this week, "
                    f"your check-in streak is {summary['checkin_streak']} day(s), and your weekly goal is {summary['weekly_goal_completion']}% complete."
                ),
                intent="weekly_summary",
                tool_name="get_weekly_summary",
                tool_status="success",
                action_payload={"summary": summary},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #dashboard query----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 💥Retrieved dashboard summary information for the user
        #for the dashboard query question
        if any(phrase in lowered for phrase in ("focus score", "brain state", "how am i doing")):
            return AgentResponse(
                reply=(
                    f"Your current focus score is {dashboard['focus_score']} and your brain state is {dashboard['current_state']}. "
                    f"{dashboard['headline']}"
                ),
                intent="dashboard_query",
                tool_name="get_dashboard_summary",
                tool_status="success",
                action_payload={"dashboard": dashboard},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #suggestion query----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 💥Retrieved suggestion information for the user
    # 🚩🚩🚩🚩🚩UPDATE TO merge between query and chat knowledge 
            #for the suggestion query question
        if any(phrase in lowered for phrase in ("best study time", "risk window", "sleep protection")):
            suggestions = repository.suggestion_engine(session["user_id"], settings)
            return AgentResponse(
                reply=(
                    f"Your best study time is around {suggestions['best_study_time']}, your sleep protection time is {suggestions['sleep_protection_time']}, "
                    f"and your risk window is {suggestions['risk_window']}."
                ),
                intent="suggestion_query",
                tool_name="get_suggestions",
                tool_status="success",
                action_payload={"suggestions": suggestions},
            )
    #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #app usage query----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # 💥Retrieved app usage summary information for the user
            #for the app usage query question
        if any(phrase in lowered for phrase in ("app usage", "most used app", "usage history", "screen time")):
            usage = repository.app_usage_summary(session["user_id"])
            if usage["apps"]:
                lead = usage["apps"][0]
                reply = f"Your most active app in the last 7 days is {lead['app_name']} with {lead['total_hours']} hours."
            else:
                reply = "You do not have app usage data yet. Add a few entries and I can analyze them for you."
            return AgentResponse(
                reply=reply,
                intent="usage_query",
                tool_name="get_app_usage_summary",
                tool_status="success",
                action_payload={"usage": usage},
            )
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # retrieve knowledge-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        retrieved = self.retrieve_context(lowered)
        if retrieved:
            lead = retrieved[0]
            return AgentResponse(
                reply=f"{lead.content} If you want, I can also make a direct change for you here.",
                intent="knowledge_answer",
                tool_name="retrieve_context",
                tool_status="success",
                retrieved_notes=retrieved,
            )

        return AgentResponse(
            reply=(
                "I can help with settings, timers, summaries, app usage, and focus insights. "
                "Try a message like 'change my session time to 45 minutes' or 'show my weekly summary.'"
            ),
            intent="fallback",
        )
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# this function is responsible for retrieving relevant knowledge from the knowledge base based on the user's message. It uses regular expressions to extract keywords from the message and compares them against the keywords associated with each piece of knowledge in the knowledge base. The function returns a list of relevant notes sorted by their relevance score.
    def retrieve_context(self, lowered_message: str) -> list[RetrievalNote]:
        tokens = {token for token in re.findall(r"[a-z0-9]+", lowered_message) if len(token) > 2}
        matches: list[RetrievalNote] = []
        for item in self.knowledge_base:
            score = len(tokens & item["keywords"])
            if score:
                matches.append(RetrievalNote(title=item["title"], content=item["content"], score=score))
        matches.sort(key=lambda note: (-note.score, note.title))
        return matches[:2]
