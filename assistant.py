"""
FreightGuard AI — Smart Assistant CLI (Stretch Goal)
Allows users/interviewers to ask plain-English questions regarding shipping costs,
corridor drift, baseline comparisons, and operational note justifications.
"""

import sys
import argparse
from rag_engine import SmartAssistant

def main():
    parser = argparse.ArgumentParser(description="FreightGuard AI Smart Assistant")
    parser.add_argument("query", nargs="*", help="Question to ask the assistant in plain English")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive Q&A REPL")
    args = parser.parse_args()

    assistant = SmartAssistant()

    if args.interactive or not args.query:
        print("=" * 65)
        print("FREIGHTGUARD AI — INTERACTIVE SMART ASSISTANT")
        print("Audits 728 route-weeks & retrieves operational note evidence.")
        print("Type 'exit' or 'quit' to terminate.")
        print("=" * 65)
        print("Sample questions:")
        print("  • Why did Delhi-Jaipur spike in November 2024?")
        print("  • Why was Ahmedabad-Mumbai justified?")
        print("  • What happened to Chennai-Bangalore in March?")
        print("  • Did the vehicle tracking mandate cause rate increases?")
        print("-" * 65)

        while True:
            try:
                user_input = input("\n[Ask Assistant] > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ('exit', 'quit', 'q'):
                    print("Exiting assistant. Goodbye!")
                    break

                res = assistant.answer_question(user_input)
                print(f"\n[FreightGuard AI · {res['corridor']}]")
                print(res['answer'])
                if res['matched_notes']:
                    print(f"\nCited Notes: {', '.join(res['matched_notes'])}")
            except (KeyboardInterrupt, EOFError):
                print("\nSession ended.")
                break
    else:
        question = " ".join(args.query)
        res = assistant.answer_question(question)
        print(f"\n[Corridor: {res['corridor']}]")
        print(res['answer'])
        if res['matched_notes']:
            print(f"\nCited Notes: {', '.join(res['matched_notes'])}")

if __name__ == '__main__':
    main()
