import functools
import traceback
from chat_server_demo.database import db
import streamlit as st

def log_this(func):
    """
    Decorator that logs function calls, results, and exceptions to the database.
    Logging failures are caught so they do not affect the main application flow.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            try:
                db.insert_log(
                    level="INFO",
                    func_name=func.__name__,
                    args=args,
                    kwargs=kwargs,
                    result=result,
                    user_id=getattr(args[0], "user_id", None) if args else None
                )
            except Exception as log_err:
                # Logging failed — swallow and continue
                st.warning("⚠️ Logging service temporarily unavailable.")
            return result
        except Exception as e:
            try:
                db.insert_log(
                    level="ERROR",
                    func_name=func.__name__,
                    args=args,
                    kwargs=kwargs,
                    exception=traceback.format_exc(),
                    user_id=getattr(args[0], "user_id", None) if args else None
                )
            except Exception as log_err:
                print(f"[LOGGING ERROR] Could not insert error log for {func.__name__}: {log_err}")
            st.warning("⚠️ Something went wrong. The app will reload.")
            st.rerun()
    return wrapper
