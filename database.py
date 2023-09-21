import sqlite3
from typing import Annotated

from fastapi import Body
from pydantic import BaseModel

QUESTION = """
    CREATE TABLE IF NOT EXISTS question(
        question_id INTEGER PRIMARY KEY AUTOINCREMENT ,
        content TEXT NOT NULL 
    )
"""

ANSWER = """
    CREATE TABLE IF NOT EXISTS answer(
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        points INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        FOREIGN KEY (question_id)
            REFERENCES question(question_id) 
            ON DELETE CASCADE 
    )
"""

SAVE_NEW_QUESTION = """
    INSERT INTO question (content) VALUES (?)
"""


class Answer(BaseModel):
    content: str
    points: Annotated[int, Body(gt=0, le=100)]


class Question(BaseModel):
    content: str
    answers: list[Answer]


class DataBase:
    def __init__(self):
        self.con = sqlite3.connect("./database.db")
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON")
        self.cur.execute(QUESTION)
        self.cur.execute(ANSWER)

    def __del__(self):
        self.con.close()

    def get_questions(self):
        self.cur.execute("SELECT * FROM question")
        return [dict(question) for question in self.cur.fetchall()]
        # return list(map(lambda q: {"question_id": q[0], "content": q[1]}, questions))

    def get_answers(self, question_id):
        self.cur.execute(
            "SELECT * FROM answer WHERE question_id = ? ORDER BY points DESC",
            (question_id,),
        )
        return [dict(answer) for answer in self.cur.fetchmany(6)]

    def add_question(self, question: Question):
        self.cur.execute(
            "INSERT INTO question (content) VALUES (?)", (question.content,)
        )
        question_id = self.cur.lastrowid
        for answer in question.answers:
            self.cur.execute(
                "INSERT INTO answer (content, points, question_id) VALUES (?, ?, ?)",
                (answer.content, answer.points, question_id),
            )

        self.con.commit()

    def remove_question(self, question_id):
        self.cur.execute("DELETE FROM question WHERE question_id = ?", (question_id,))
        self.con.commit()

    def update_answers(
        self, question_id: int, answers: Annotated[list[Answer], Body()]
    ):
        self.cur.execute(
            "SELECT answer_id FROM answer WHERE question_id = ? ORDER BY answer_id",
            (question_id,),
        )
        ids = self.cur.fetchall()
        if len(ids) > len(answers):
            self.cur.execute(
                "DELETE FROM answer WHERE answer_id IN (SELECT answer_id FROM answer WHERE question_id = ? ORDER BY answer_id DESC LIMIT ? )",
                (question_id, len(ids) - len(answers)),
            )

        for i, answer in enumerate(answers):
            if i < len(ids):
                self.cur.execute(
                    "UPDATE answer SET content = ?, points = ? WHERE answer_id = ?",
                    (answer.content, answer.points, ids[i]["answer_id"]),
                )
            else:
                self.cur.execute(
                    "INSERT INTO answer (content, points, question_id) VALUES (?, ?, ?)",
                    (answer.content, answer.points, question_id),
                )

        self.con.commit()
