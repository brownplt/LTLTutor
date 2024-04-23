import express from 'express';
import path from 'path';
import {LTLNode, parseLTLString} from './ltlnode';
import {getAllApplicableMisconceptions} from './codebook';

const app = express();
const port = 5000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.static('public'));
app.use(express.urlencoded({ extended: true }));

app.get('/qgen', (req, res) => {
    // Handle GET request
    let distractors = [];
    res.render('qgen', {distractors: distractors});
});



app.post('/qgen', (req, res) => {
    // Handle form POST request
    // Access form data using req.body
    
    const formData = req.body;
    const answer = formData.answer;

    // Parse the LTL string
    try {
        const ltl = parseLTLString(answer);
        const d = getAllApplicableMisconceptions(ltl);
        let  distractors=  d.map(d => ({
            "formula": d.node.toString(),
            "code": d.misconception.toString()
        }));

        // Merge labels for equal formulae
        const mergedDistractors = [];
        for (const distractor of distractors) {
            const existingDistractor = mergedDistractors.find(d => d.formula === distractor.formula);
            if (existingDistractor) {
                existingDistractor.code += `, ${distractor.code}`;
            } else {
                mergedDistractors.push(distractor);
            }
        }
        distractors = mergedDistractors;

        
        if (distractors.length === 0) {
            distractors.push({
                "formula": "-",
                "code": "No applicable misconceptions"
            });
        }
        res.render('qgen',{"distractors": distractors, error: ""});
    }
    catch (e) {

        let distractors = [{
                "formula": "-",
                "code": "Invalid LTL formula"
            }];


        res.render('qgen', { error: 'Invalid LTL formula', distractors: distractors});
        return;
    }
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});