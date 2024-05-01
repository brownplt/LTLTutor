import spotutils


class FeedbackGenerator:

    def __init__(self, correct, student):
        self.correct_answer = correct
        self.student_selection = student


    def isSubsumed(self):
        return spotutils.isNecessaryFor(self.correct_answer, self.student_selection)
    
    def isContained(self):
        return spotutils.isNecessaryFor(self.student_selection, self.correct_answer)
    
    def disjoint(self):
        return spotutils.areDisjoint(self.correct_answer, self.student_selection)


    def getCEWords(self):
        if self.disjoint():
            return spotutils.generate_traces(self.student_selection)
        elif self.isSubsumed():
            return spotutils.generate_traces(f_accepted=self.correct_answer, f_rejected=self.student_selection)
        elif self.isContained():
            return spotutils.generate_traces(f_accepted=self.student_selection, f_rejected=self.correct_answer)
        else:
            return []

