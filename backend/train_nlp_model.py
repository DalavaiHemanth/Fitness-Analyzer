"""
NLP Intent Classifier Training Script  (v2 — High Accuracy Edition)
=====================================================================
Trains an ensemble of TF-IDF + LR / SVM / LinearSVC classifiers.
Target: >95% test accuracy on intent classification.

Categories: strength, cardio, flexibility, recovery

Usage:
  python train_nlp_model.py
"""
import os
import sys
import json
import logging
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import VotingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_OUTPUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "nlp_intent_classifier.pkl")
REPORT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "nlp_training_report.json")
CUSTOM_DATA   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets",  "nlp_training_data.json")

# ── MASSIVELY EXPANDED training corpus (5× larger per class) ──────────────────
TRAINING_DATA = {
    "strength": [
        # Pushup/push variants
        "I did 3 sets of 10 pushups", "Completed 50 push-ups", "Did push-ups until failure",
        "4 sets of wide-grip pushups", "Diamond push-ups 3x15", "Incline push-ups on the bench",
        # Bench press
        "Completed 4 sets of 8 bench press at 80kg", "Flat bench press 5x5 at 100kg",
        "Incline dumbbell press 4x10", "Decline barbell press 3x8", "Close grip bench for triceps",
        "Bench pressed 3 reps at 120kg", "Machine chest press 3 sets",
        # Bicep
        "Bicep curls with dumbbells, 3 sets of 12", "Hammer curls and concentration curls",
        "Preacher curls 3x10 at 15kg", "Barbell curl 4 sets of 8", "Cable curls 3x15",
        "EZ-bar curls 3 sets", "Reverse curls for forearm development",
        # Squat
        "Squat session today: 5 sets of 5 reps at 100kg", "Back squats 4x6 at 90kg",
        "Front squats 3x8 with barbell", "Goblet squats with kettlebell", "Box squats 4x5",
        "Bulgarian split squats 3x10 each leg", "Pause squats at 80kg", "Heavy squats followed by leg curls",
        "Hack squats on the machine", "Leg press 4 sets of 12",
        # Deadlift
        "Deadlift 120kg for 3 reps, 4 sets", "Romanian deadlifts 3x10", "Sumo deadlift 5x3",
        "Trap bar deadlift session", "Stiff-legged deadlifts for posterior chain",
        "Conventional deadlift up to 150kg", "Single leg deadlifts 3x12",
        # Pull up / Row
        "Did pull-ups and rows for back day", "Weighted pull-ups 4x6", "Wide grip pull-ups 3x10",
        "Lat pulldown and seated rows", "Barbell rows 3x8 at 70kg", "Dumbbell rows 4x12 each side",
        "T-bar rows and wide-grip pullups", "Cable rows 3x15", "Kroc rows 3 sets",
        # Shoulder press
        "Shoulder press 50kg, 4 sets of 8", "Military press 4 sets of 6 reps",
        "Arnold press 3x10 with 20kg", "Seated dumbbell press 4x10",
        "Overhead press 3x5 at 60kg", "Lateral raises and front raises 3x15",
        # Lunges / legs
        "Leg press and lunges today", "Walking lunges 3 sets of 20 steps",
        "Weighted lunges in the squat rack", "Reverse lunges with dumbbell", "Step-ups 3x12",
        "Leg extensions and hamstring curls, 4 sets each", "Leg curls 4x12",
        "Calf raises 5 sets of 20 reps",
        # Tricep / Chest
        "Chest day: bench, flyes, and dips", "Dips and skull crushers", "Tricep pushdowns 3x15",
        "Overhead tricep extension 4x12", "Close grip bench press to target triceps",
        "Pec deck flyes 3x15", "Cable crossovers 4x12",
        # Abs / Core
        "Core workout: crunches sit-ups planks", "Plank holds for 60 seconds, 3 sets",
        "Hanging leg raises 3x15", "Russian twists 4 sets", "Dragon flags 3x8",
        "Ab wheel rollouts 3x10", "Cable crunches 4x15", "Weighted crunches 3x20",
        # General compound
        "Heavy compound lifts today", "Full body strength workout",
        "Back workout: T-bar rows and wide-grip pullups", "Chest and triceps day",
        "Legs and glutes session", "Push day at the gym", "Pull day workout completed",
        "Upper body strength training", "Lower body compound movements",
        "Chest, shoulders, and triceps", "Back and biceps training",
        "Barbell shrugs for traps, 3 sets of 15", "Hip thrusts 4x10",
        "3x12 incline dumbbell press", "Maximum effort on the pec deck today",
        "Cable rows and pull-ups for 4 sets", "Dumbbell curls and tricep extensions",
        "Weighted dips and push-ups", "Front squats 4x6 at 80kg",
        "Barbell rows 3x8 at 70kg", "Romanian deadlifts and hip thrusts",
        "Military press 4 sets of 6 reps", "Cable rows and pull-ups for 4 sets",
        "5 sets of heavy deadlifts", "3 reps max on the bench today",
        "Worked out at the gym, heavy lifting", "Resistance training full body",
        "Strength workout with barbells and dumbbells", "Lifting session: heavy sets",
        "4x8 on all compound lifts today", "Kettlebell swings 5x20",
        "Bulgarian split squat 3x10", "Hip thrust 4x12 with 80kg",
    ],
    "cardio": [
        # Running
        "Ran 5km in 30 minutes", "45 minute jog in the park", "Morning run 8km",
        "10km run in 52 minutes", "5 mile run in the morning", "Cross country run 10km",
        "Jogged to the gym and back", "Evening run 6km easy pace",
        "Sprint intervals on the track", "400m repeats 8 times",
        "Interval training 1 minute sprint rest", "Hill sprints 10 rounds",
        "Tempo run 5km at threshold pace", "Easy recovery jog 20 minutes",
        "Ran for 1 hour at moderate pace", "Treadmill run 8km per hour for 40 minutes",
        "9km long run on Sunday", "15km marathon training run",
        # Cycling / Bike
        "Cycling for 1 hour at moderate pace", "20 minute bike ride",
        "Mountain bike ride for 2 hours", "Cycling class at the gym today",
        "40 minute cycling class", "Stationary bike 45 minutes",
        "Spin class 60 minutes high intensity", "Road cycling 30km today",
        # HIIT
        "HIIT session: 20 minutes high intensity", "HIIT on the treadmill 25 minutes",
        "30 minute cardio kickboxing", "Tabata training 4 rounds",
        "Burpees and jumping jacks circuit", "High intensity interval workout",
        "HIIT cardio for fat burning", "Circuit training with cardio",
        # Swimming
        "Swimming laps for 30 minutes", "Swam 1km breaststroke",
        "Freestyle swim 40 lengths", "Open water swim 2km",
        "Pool laps for cardio conditioning", "Swimming for cardiovascular fitness",
        # Jump rope / other
        "Jump rope 10 minutes then sprints", "Jumped rope for 15 minutes straight",
        "Skipping rope 1000 jumps", "Step aerobics class 45 minutes",
        # Walking
        "Brisk walk for 60 minutes", "Stair climbing 20 minutes",
        "Easy 20 minute walk for active recovery", "Walked 12000 steps today",
        "Hiking 5km mountain trail", "Inclined treadmill walk 30 minutes",
        # Rowing / Elliptical
        "Rowing machine 500 meters 5 times", "Elliptical machine 30 minutes",
        "Rowing for 20 minutes steady state", "Concept2 rower 2k time trial",
        # General
        "Aerobic dance class 45 minutes", "Cardio session completed",
        "Cardio workout for heart health", "Kept heart rate elevated for 45 minutes",
        "Fat burning cardio session", "40 minutes of pure cardio",
        "Zone 2 cardio 60 minutes", "Steady state cardio on the bike",
        "Warm up jog followed by sprints", "Long distance endurance training",
        "Sprinted 200m intervals 8 times", "Fasted cardio in the morning",
        "Treadmill intervals 1 min on 1 min off", "Cardio for 50 minutes at 65% max HR",
        "Aerobic base building run today", "Cardio kickboxing for conditioning",
    ],
    "flexibility": [
        # Yoga variants
        "Morning yoga session 30 minutes", "Yoga flow for 20 minutes",
        "Hot yoga class 60 minutes", "Yin yoga 40 minutes", "Power yoga flow 30 minutes",
        "Ashtanga yoga primary series", "Gentle yoga for stress relief",
        "Restorative yoga with props", "Yoga for core strength and balance",
        "Back bending and spine decompression yoga", "Vinyasa flow yoga 45 minutes",
        "Hatha yoga beginner class", "Bikram yoga 90 minutes hot room",
        "Sun salutations for 15 minutes", "Kundalini yoga for relaxation",
        "Yoga nidra for deep relaxation", "Morning sun salutation sequence",
        "Warrior sequence and pigeon pose", "Yin yang yoga 60 minutes",
        # Stretching
        "Stretching routine before bed", "Full body stretch session",
        "Hip flexor and hamstring stretches", "Post-workout static stretches",
        "Stretching after long run", "Dynamic warm-up routine",
        "Full body stretching routine", "Neck and shoulder mobility routine",
        "Splits training and hip opening", "Cat-cow and thread the needle stretches",
        "Pigeon pose and lizard lunge for hips", "Shoulder mobility drills before lifting",
        "Active stretching for athletic performance", "Deep breathing and stretching for 20 mins",
        "Upper body stretching after workout", "Lower body flexibility routine",
        "IT band rolling and hip stretches", "Calf and achilles stretches",
        "Prone cobra and child's pose sequence", "Spinal mobility and thoracic rotation",
        # Pilates
        "Pilates class for 45 minutes", "Pilates reformer session",
        "Mat pilates for core and flexibility", "Pilates for posture improvement",
        "Chair pilates 30 minutes", "Pilates hundred and roll-ups 3 sets",
        # Mobility
        "Foam rolling and mobility work", "Balance and flexibility exercises",
        "Full body mobility session with a stick", "Joint mobility drill routine",
        "Mobility drills and joint rotations", "Hip mobility and IT band work",
        "Ankle and wrist mobility circuit", "Thoracic mobility 20 minutes",
        "Prehab mobility work before training", "Corrective flexibility exercises",
        # Foam rolling
        "Foam rolled my entire back and legs", "Foam rolling tight spots",
        "Foam roller for IT band and quads", "Myofascial release with foam roller",
        "Deep tissue foam rolling session", "Rolling out sore muscles",
        # General
        "Flexibility training with resistance bands",
        "Downward dog warrior pose sequence", "Worked on flexibility and mobility",
        "Open hips and stretch tight areas", "Yoga and stretching for recovery",
        "Active flexibility work 30 minutes", "Barre class for flexibility",
        "Dance stretching and splits practice",
    ],
    "recovery": [
        # Pure rest
        "Rest day today", "Complete rest, focusing on sleep",
        "Taking the day off to recover", "No workout today, body needed rest",
        "Rest day with meal prep", "Today was a full rest day",
        "Completely rested, no exercise", "Off day for recovery",
        "Passive rest day, no activity", "Took a rest day from training",
        "Body rest and recuperation day", "Mental and physical rest day",
        # Light activity / walk
        "Light recovery walk in the evening", "Just walking around today",
        "Easy 20 minute walk for active recovery", "Short walk to keep joints moving",
        "Enjoying a slow walk and fresh air", "Gentle stroll for blood flow",
        "Recovery swim at low intensity", "Easy swim for active recovery",
        "Light cycling 15 minutes very easy", "Slow easy movement only today",
        "Active rest: playing light frisbee", "Walking the dog gently",
        # Massage / bodywork
        "Sports massage for sore muscles", "Had a massage and relaxed",
        "Epsom salt bath for muscle soreness", "Cold shower and stretching",
        "Ice bath after training", "Ice pack on my knee after training",
        "Contrast shower hot cold for recovery", "Heat pad on aching muscles",
        "Roller massage and soft tissue work", "Percussion massage gun session",
        "Deep tissue massage booked", "Self myofascial release therapy",
        # Sleep / nutrition focus
        "Sleep and nutrition focus day", "Just resting and staying hydrated",
        "Hydration and stretching focus today", "8 hours sleep and meal prep only",
        "Early to bed, total rest", "Prioritizing sleep for muscle repair",
        "Rest and high protein meals today", "Recovery nutrition and sleep focus",
        # Deload
        "Deload week light movements", "Deload week, just light movement",
        "Taking a break from the gym for a few days", "Easy deload session 50% weight",
        "Deload: light weights and high reps", "Back off week from heavy lifting",
        # Meditation / mental
        "Meditation and light movement for recovery", "Recharging my batteries with total rest",
        "Mindfulness and breathing exercises", "Yoga nidra for recovery",
        "Breath work and relaxation session", "10 minute meditation only today",
        # Focusing on blood flow
        "Focusing on mobility and blood flow only", "Easy movement to promote blood flow",
        "Recovery session with yoga", "Gentle stretches to flush out DOMS",
        "Very light activity to help soreness", "Recovery modalities: ice bath + massage",
        "Compression boots on for 30 minutes", "Physiotherapy exercises only",
        "Light rehab after injury", "Easy physio session for knee recovery",
    ],
}


def build_dataset():
    """Build training arrays from synthetic + custom data."""
    texts, labels = [], []
    for intent, samples in TRAINING_DATA.items():
        for text in samples:
            texts.append(text)
            labels.append(intent)

    if os.path.exists(CUSTOM_DATA):
        logger.info("Loading custom training data from %s", CUSTOM_DATA)
        with open(CUSTOM_DATA) as f:
            custom = json.load(f)
        for intent, samples in custom.items():
            for text in samples:
                texts.append(text)
                labels.append(intent)
        logger.info("Added %d custom samples", sum(len(v) for v in custom.values()))

    logger.info("Total samples: %d across %d classes", len(texts), len(set(labels)))
    return np.array(texts), np.array(labels)


def train(texts, labels):
    """Train an ensemble of TF-IDF pipelines and evaluate performance."""
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.15, stratify=labels, random_state=42
    )

    # ── Feature extractor: word n-grams + char n-grams combined ──────────────
    word_tfidf = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 3),
        max_features=8000,
        sublinear_tf=True,
        min_df=1,
        strip_accents="unicode",
        lowercase=True,
    )
    char_tfidf = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=6000,
        sublinear_tf=True,
        min_df=1,
        strip_accents="unicode",
        lowercase=True,
    )
    features = FeatureUnion([
        ("word", word_tfidf),
        ("char", char_tfidf),
    ])

    # ── Individual classifiers (all wrapped for probability output) ───────────
    lr = Pipeline([
        ("feat", features),
        ("clf", LogisticRegression(
            solver="lbfgs", max_iter=2000, C=5.0,
            class_weight="balanced", multi_class="multinomial"
        )),
    ])

    svm = Pipeline([
        ("feat", features),
        ("clf", CalibratedClassifierCV(
            LinearSVC(max_iter=3000, C=2.0, class_weight="balanced"), cv=5
        )),
    ])

    svc = Pipeline([
        ("feat", features),
        ("clf", SVC(
            kernel="rbf", C=10.0, gamma="scale", probability=True,
            class_weight="balanced"
        )),
    ])

    # ── Soft-voting ensemble ──────────────────────────────────────────────────
    ensemble = VotingClassifier(
        estimators=[("lr", lr), ("svm", svm), ("svc", svc)],
        voting="soft",
        weights=[2, 1, 2],   # LR and SVC get more weight
    )

    logger.info("Training ensemble (LR + LinearSVC + RBF-SVC)...")
    ensemble.fit(X_train, y_train)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(ensemble, X_train, y_train, cv=skf, scoring="accuracy")
    test_acc = accuracy_score(y_test, ensemble.predict(X_test))
    report = classification_report(y_test, ensemble.predict(X_test), output_dict=True)

    logger.info("CV accuracy: %.3f ± %.3f", cv_scores.mean(), cv_scores.std())
    logger.info("Test accuracy: %.3f", test_acc)
    logger.info("\n%s", classification_report(y_test, ensemble.predict(X_test)))

    training_report = {
        "cv_mean":  round(float(cv_scores.mean()), 4),
        "cv_std":   round(float(cv_scores.std()), 4),
        "test_accuracy": round(test_acc, 4),
        "classification_report": report,
        "num_samples": len(texts),
        "model_type": "VotingEnsemble(LR+LinearSVC+RBF-SVC) + word+char TF-IDF",
    }
    return ensemble, training_report


def main():
    logger.info("=== NLP Intent Classifier Training v2 ===")
    texts, labels = build_dataset()
    model, report = train(texts, labels)

    os.makedirs(os.path.dirname(MODEL_OUTPUT), exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    logger.info("💾 NLP model saved to: %s", MODEL_OUTPUT)

    with open(REPORT_OUTPUT, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("📊 NLP report saved: %s", REPORT_OUTPUT)
    logger.info("✅ Test accuracy: %.1f%%", report["test_accuracy"] * 100)


if __name__ == "__main__":
    main()
