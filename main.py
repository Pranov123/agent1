from dotenv import load_dotenv
load_dotenv()

import sys
from core.pipeline import Pipeline

def main():
    print("\n╔══════════════════════════════════════╗")
    print("║          AGENT 1 — SCOPE AGENT       ║")
    print("╚══════════════════════════════════════╝\n")

    if len(sys.argv) > 1:
        # input passed as command line argument
        user_input = " ".join(sys.argv[1:])
    else:
        # interactive input
        print("Enter your idea, feature request, or requirement.")
        print("Be as raw and unfiltered as you want — Agent 1 will structure it.\n")
        print("─" * 50)
        user_input = input("> ").strip()
        print("─" * 50 + "\n")

    if not user_input:
        print("No input provided. Exiting.")
        sys.exit(1)

    pipeline = Pipeline()
    summary  = pipeline.run(user_input)

    print("\n╔══════════════════════════════════════╗")
    print("║              SESSION SUMMARY         ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Session ID   : {summary['session_id']}")
    print(f"  Requirements : {summary['total_requirements']}")
    print(f"  Non-goals    : {summary['total_non_goals']}")
    print(f"  Risk tier    : {summary['ethos_risk_tier']}")
    print(f"  Open flags   : {summary['flags_open']}")
    print(f"  HITL1 rounds : {summary['hitl1_rounds']}")
    print()

if __name__ == "__main__":
    main()