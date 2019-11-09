import os
import sys
import argparse
import subprocess
import time
import shutil
import random
import logging

import apscheduler
import apscheduler.schedulers.background
from apscheduler.executors.pool import ProcessPoolExecutor

from pymongo import MongoClient

from common import play

DIR = "./sandbox"
SOLUTIONS = os.path.join(DIR, "solutions")
BINARIES = os.path.join(DIR, "binaries")

for path in (SOLUTIONS, BINARIES):
    if not os.path.exists(path):
        os.makedirs(path)


def compile(solution, timestamp):
    binary = os.path.join(BINARIES, "{}_{}".format(os.path.splitext(solution)[0], timestamp))
    subprocess.check_output(["c++", "-O3", "--std=c++14", solution, "-o", binary])
    return binary


def play_one_game():
    client = MongoClient()
    db = client["sandbox"]
    solutions = list(db.solutions.find())
    if len(solutions) < 2:
        print "Not enough solutions to play"
        return

    solutions = random.sample(solutions, 2)
    # print solutions
    binaries = [s["binary"] for s in solutions]
    print("Playing {}".format(binaries))
    winner = play(*binaries)
    print("Winner: {}".format(winner))
    if winner == -1:
        solution = solutions[0]["solution"]
        db.results.update_one({"solution": solution}, {"$inc": {"wins.{}".format(0): 1}})
        solution = solutions[1]["solution"]
        db.results.update_one({"solution": solution}, {"$inc": {"wins.{}".format(0): 1}})
    else:
        solution = solutions[0]["solution"]
        db.results.update_one({"solution": solution}, {"$inc": {"wins.{}".format(winner): 1}})
        solution = solutions[1]["solution"]
        db.results.update_one({"solution": solution}, {"$inc": {"wins.{}".format(3 - winner): 1}})


def main():
    parser = argparse.ArgumentParser(description="Sandbox")
    parser.add_argument("--post", nargs="+", help="<solution> [comment]")
    parser.add_argument("--run", action="store_true", help="run sandbox")
    parser.add_argument("--clean", action="store_true", help="clean results")
    parser.add_argument("--initialize", action="store_true", help="reinitialize *EVERYTHING*")

    args = parser.parse_args()

    client = MongoClient()
    db = client["sandbox"]

    if args.post:
        timestamp = int(time.time())
        solution = args.post[0]
        comment = args.post[1] if len(args.post) > 1 else "no comment"
        binary = compile(solution, timestamp)
        basename, extension = os.path.splitext(solution)
        new_solution = os.path.join(SOLUTIONS, "{}_{}{}".format(basename, timestamp, extension))
        shutil.copy(solution, new_solution)
        db.solutions.insert_one({"solution": new_solution, "comment": comment, "binary": binary})
        db.results.insert_one({"solution": new_solution, "wins": [0, 0, 0]})
    elif args.run:
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        scheduler = apscheduler.schedulers.background.BackgroundScheduler(
            executors={"processpool": ProcessPoolExecutor(12)},
            job_defaults={"max_instances": 12}
        )
        scheduler.add_job(play_one_game, "interval", seconds=0.7)
        try:
            scheduler.start()
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            return
    elif args.clean:
        db.results.update_many({}, {"$set": {"wins": [0, 0, 0]}})
    elif args.initialize:
        db.solutions.remove({})
        db.results.remove({})
        shutil.rmtree(DIR)
    else:
        comment = {}
        for rec in db.solutions.find():
            comment[rec["solution"]] = rec["comment"]
        for rec in db.results.find():
            print rec["solution"], "\t", rec["wins"], comment[rec["solution"]]


if __name__ == "__main__":
    main()
