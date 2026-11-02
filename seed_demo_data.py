import os
from config import BASE_DIR, AUDIO_DIR
from services.speech_service import synthesize_speech
import db

def seed_multilingual_assets():
    print("Generating multilingual demo assets...")
    db.init_db()
    
    samples = [
        # Marathi
        ("sample_reminder_mr.wav", "नमस्कार पाटील काका, तारीख ॲपवरून फोन आहे. परवा चौदा नोव्हेंबरला हवेली कोर्टात तुमची जमीन दाव्याची सुनावणी आहे. मूळ खरेदी खत आणि सात बारा उतारा सोबत आणायला विसरू नका. धन्यवाद.", "mr-IN", "rohan"),
        ("sample_lawyer_mr.wav", "पाटील साहेब, काळजी करू नका. आज कोर्टात आपलं एविडन्स पूर्ण झालं आहे. पुढची तारीख साहेबांनी ऑर्डरसाठी ठेवली आहे.", "mr-IN", "aditya"),
        
        # Hindi
        ("sample_reminder_hi.wav", "नमस्ते पाटिल जी, तारीख ऐप से कॉल है। आगामी 14 नवंबर को हवेली अदालत में आपकी जमीन मामले की सुनवाई है। मूल बिक्री विलेख और 7/12 खतौनी साथ लाना न भूलें।", "hi-IN", "aditya"),
        ("sample_lawyer_hi.wav", "पाटिल साहब, नमस्कार। आज कोर्ट में अपना सबूत और एविडेंस पूरा दर्ज हो गया है। जज साहब ने अगली तारीख फैसले के लिए रखी है, चिंता न करें।", "hi-IN", "aditya"),
        
        # English
        ("sample_reminder_en.wav", "Hello Mr. Patil, this is your Tareekh reminder call. Your civil court hearing is scheduled on 14th November at Haveli Court. Please remember to bring your original registered sale deed and 7/12 extract.", "en-IN", "aditya"),
        ("sample_lawyer_en.wav", "Hello Patil sir, do not worry. Today in court our evidence stage was fully completed. The judge has scheduled the next date directly for final orders.", "en-IN", "aditya"),
    ]
    
    for filename, text, lang, speaker in samples:
        dest_file = AUDIO_DIR / filename
        if not dest_file.exists():
            print(f"Synthesizing {filename} ({lang})...")
            try:
                path, _ = synthesize_speech(
                    text=text,
                    language_code=lang,
                    speaker=speaker,
                    filename_prefix=filename.split(".")[0]
                )
                if os.path.exists(path):
                    os.replace(path, str(dest_file))
                    print(f"Saved: {dest_file}")
            except Exception as e:
                print(f"Error synthesizing {filename}: {e}")

if __name__ == "__main__":
    seed_multilingual_assets()
