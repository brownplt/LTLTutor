import spotutils


class FeedbackGenerator:

    def __init__(self, correct, student):
        self.correct_answer = correct
        self.student_selection = student


    def correctAnswerContained(self):
        # correct answer => student selection
        return spotutils.isSufficientFor(self.correct_answer, self.student_selection)
    
    def correctAnswerSubsumes(self):
        # student selection => correct answer
        return spotutils.isSufficientFor(self.student_selection, self.correct_answer)
    
    def disjoint(self):
        return spotutils.areDisjoint(self.correct_answer, self.student_selection)


    def getCEWords(self):
        if self.disjoint():
            return spotutils.generate_accepted_traces(self.student_selection)
        elif self.correctAnswerSubsumes():
            return spotutils.generate_traces(f_accepted=self.correct_answer, f_rejected=self.student_selection)
        elif self.correctAnswerContained():
            return spotutils.generate_traces(f_accepted=self.student_selection, f_rejected=self.correct_answer)
        ### What about the case where there is partial overlap.
        else:
            return spotutils.generate_traces(f_accepted=self.student_selection, f_rejected=self.correct_answer)

