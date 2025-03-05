import time
import json
import psutil
import argparse
from llama_cpp import Llama
from datetime import datetime

def get_cpu_metrics():
    try:
        temp = psutil.sensors_temperatures()["cpu_thermal"][0].current
        freq = psutil.cpu_freq().current
        return temp, freq
    except Exception as e:
        print(f"Error reading CPU metrics: {e}")
        return None, None

def load_model(model_path, n_ctx=4096, n_threads=4):
    print("Loading the model...")
    try:
        llm = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)
        print("Model Loaded Successfully")
        return llm
    except Exception as e:
        print(f"Error loading the model: {e}")
        return None

def run_inference(llm, sequence, max_tokens, temperature=1.0):
    temp_before, freq_before = get_cpu_metrics()
    start_time = time.time()

    try:
        output = llm(
            sequence,
            echo=True,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            top_k=40
        )
        elapsed_time = time.time() - start_time
        total_tokens = output.get('usage', {}).get('total_tokens', 0)
        completion_tokens = output.get('usage', {}).get('completion_tokens', 0)
        token_rate = total_tokens / elapsed_time if elapsed_time > 0 else 0
        temp_after, freq_after = get_cpu_metrics()
        generated_text = output['choices'][0]['text'].strip()

        # Output results
        result_data = {
            "sequence": sequence[:50] + "...",
            "max_tokens": max_tokens,
            "elapsed_time": elapsed_time,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "token_rate": token_rate,
            "cpu_temp_before": temp_before,
            "cpu_temp_after": temp_after,
            "cpu_freq_before": freq_before,
            "cpu_freq_after": freq_after,
            "response": generated_text
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/home/rise/models/scripts/python/gguf/results/max_tokens_variation_10/max_token_run_results_{max_tokens}_tokens_{timestamp}.json"

        print(json.dumps(result_data, indent=4))
        with open(filename, "w") as f:
            json.dump(result_data, f, indent=4)

        print(f"Results saved to {filename}")
        return result_data

    except Exception as e:
        print(f"Error during inference: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLaMA inference.")
    parser.add_argument("--max_tokens", type=int, required=True, help="Maximum number of tokens.")
    args = parser.parse_args()

    MODEL_PATH = "/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
    # "/home/rise/Downloads/Llama-3.2-3B-Q4_0.gguf" 
    # "/home/rise/Downloads/llama-2-7b-chat.Q4_0.gguf"
    # "/home/rise/Downloads/Llama-3.2-3B-Q4_0.gguf" 
    test_sequence = (
    "Translate this german to english : wecken — arouse, awaken, rouse, wake, waken, wake up - cause to sleep - affect - freshen, refresh, refreshen - befruchten, fruchtbar machen — fecundate, fertilise, fertilize, inseminate - indispose - weinen — cry - etiolate - animalise, animalize, brutalise, brutalize - umwandeln — convert - opalise, opalize - arterialise, arterialize - get, make - counterchange, interchange, transpose - vascularise, vascularize - decrepitate - suburbanise, suburbanize - revolutionieren — overturn, revolutionise, revolutionize - etiolate - barbarise, barbarize - alkalinise, alkalinize - mythicise, mythicize, mythologise, mythologize - allegorise, allegorize - entmytologisieren — demythologise, demythologize - bring, land - coarsen - auswirken auf, tangieren — affect, bear on, bear upon, impact, touch, touch on - alchemise, alchemize - alcoholise, alcoholize - ausformen, formen, gestalten, verformen — form, shape - abrunden — round, round down, round off, round out - aufhängen — suspend - ernüchtern — sober - reconstruct - anheben, aufstocken, ausbreiten, ausdehnen, ausweiten, erhöhen, erweitern, heraufsetzen, mehren, steigern, verbreitern, vergrößern, vermehren — add to, augment, boost, broaden, enlarge, expand, extend, heighten, increase, raise, spread, up, widen - ease off, ease up, let up - assimilieren — assimilate - dissimilate - umwandeln — commute, convert, exchange - vitalise, vitalize - reinigen — clear, unclutter - auslösen — activate - activate - activate, aerate - activate - deactivate, inactivate - abstumpfen, abtöten, verblöden, verdummen — blunt, deaden, dull - umformen, umgestalten — reconstruct, redo, remodel - bearbeiten, edieren, editieren, herausgeben — edit, redact - herausnehmen, herausschneiden, herausstreichen — cut, edit, edit out - chasten, subdue, tame - chasten, moderate, temper - aufbessern, aufsteigen, bessern, fördern, verbessern — ameliorate, amend, better, improve, improve on, meliorate - erschweren, verschlimmern — aggravate, exacerbate, exasperate, make worse, worsen - befeuchten, durchnässen, nässen, naßmachen, nass machen — wet - abtrocknen, fönen, trocknen — dry, dry out, dry up, wipe dry - lubricate - befestigen, verstärken — beef up, fortify, reinforce, strengthen - fortify, lace, spike - schwächen — weaken - blunt - oxidieren — oxidate, oxidise, oxidize - vereinigen — merge, unify, unite - altern — age - heranreifen — mature, ripen - antiquate, antique - antiquate - develop, make grow - dämpfen — soften - benachteiligen, beschädigen, lädieren, schaden, Schaden zufügen, schädigen, schlecht sein für, verschlechtern — be bad for, cause damage, cause damage to, damage, do damage, do harm, harm, impair, injure, prejudice, put at a disadvantage - ossify - acerbate - stabilisieren, stützen — firm up, stabilise, stabilize, steady - destabilisieren, entstabilisieren — destabilise, destabilize - sensibilise, sensibilize, sensify, sensitise, sensitize - desensitise, desensitize - gewöhnen — accustom, habituate - durcheinanderbringen, durcheinander bringen, in Unordnung bringen, verwirren — disarrange, disarray, disorder, disturb, make a mess of, mess up, upset - verfärben — discolor, discolour - ausmalen, färben — color, color in, colorise, colorize, colour, colour in, colourise, colourize - beschmutzen — stain - hue - hässlich machen, verunstalten — uglify - untune - einstellen — adjust, correct, set - stellen — set - disqualify, indispose, unfit - bändigen, zähmen — domesticate, domesticise, domesticize, reclaim, tame - widen - dehydrogenate, dehydrogenize - hydrieren — hydrogenate, hydrogenize - oxygenise, oxygenize - verdunkeln — darken - erhellen — brighten, lighten, lighten up - betrüben, verschwommen machen — blear, blur - verbergen — blot out, hide, obliterate, obscure, veil - auslöschen, verhüllen — blot out, hide, obliterate, obscure, veil - kochen — cook - slenderise, slenderize - krachen — crack - dismiss, dissolve - beenden, beendigen, enden, terminieren — end, terminate - defog, demist - concentrate, condense, contract - abkühlen, erkälten, kühlen — chill, cool, cool down, cool off - erhitzen, -wärmen — heat, heat up - aufheizen, einheizen, erhitzen, erwärmen, feuern, heizen, wärmen — heat, heat up, warm, warm up - boil - einfrieren — freeze - Blasen hervorrufen — blister - schalten — change over, shift, switch - transpose - konvertieren — change over, convert - transform - transform - transform - transmute - modifizieren, transformieren, überführen, umbauen, umbilden, umformen, umsetzen, umwandeln, verwandeln — modify, remodel, transform, transmute, transubstantiate - ash - transform, translate - reclaim, rectify, reform, regenerate - bekehren, belehren, missionieren — convert, proselytize - Islamise, Islamize - umkehren, umkrempeln — invert, reverse, turn back - invert - speziell anfertigen — customise, customize - persönlich auffassen, persönlich empfinden — individualise, individualize, personalise, personalize - entpersönlichen, professioneller gestalten, versachlichen — depersonalise, depersonalize, make businesslike, make professional, objectify, professionalise, professionalize - sharpen - drop, flatten - disintegrate - magnetisieren — magnetise, magnetize - degauss, demagnetise, demagnetize - simplifizieren, vereinfachen, vereinfacht darstellen, versimpeln — simplify, streamline - komplizieren — complicate, elaborate, rarify, refine - refine - komplizieren — complicate, perplex - pressurise, pressurize, supercharge - zentralisieren — centralise, centralize, concentrate - dezentralisieren — decentralise, decentralize, deconcentrate - socialise, socialize - bereiten, herrichten, rüsten, vorbereiten, wappnen — fix, gear up, prepare, ready, set, set up - internationalise, internationalize - bolshevise, bolshevize, communise, communize - Europeanise, Europeanize - Europeanise, Europeanize - bestialise, bestialize - Americanise, Americanize - Frenchify, gallicize - civilise, civilize - entprivatisieren, nationalisieren, verstaatlichen, volkseigen machen — nationalise, nationalize - entstaatlichen, privatisieren — denationalise, denationalize - naturalise, naturalize - denaturalise, denaturalize - naturalise, naturalize - denaturalise, denaturalize - even, even out - angleichen, egalisieren, gleichkommen — equal, equalise, equalize, equate, match - festigen — stiffen - abnehmen, aufdrehen, aufmachen, lockern, losdrehen, lösen, losmachen — detach, loose, loosen, release, slacken, undo, unfasten - anspannen — fasten, tighten - transitivise, transitivize - detransitivise, detransitivize, intransitivise, intransitivize - verdicken — inspissate, thicken - full - abwechslungsreich gestalten, diversifizieren, verändern — diversify - deaden - check, delay, retard - beschneiden, herunterschrauben, kürzen, mindern, mindern um, verkleinern, vermindern, vermindern um, verringern, verringern um — curtail, cut back, cut back on, cut down, cut down on, decrease, decrease by, diminish, lessen, minify, minimise, minimize, reduce, skimp, skimp on, stint, stint on - liqueszieren, zermahlen — liquefy, liquidise, liquidize, liquify - solvate - dissolve - validate - invalidate, vitiate, void - ausleeren, entleeren, leeren — empty - abfüllen, anfüllen, auffrischen, auffüllen, ausfüllen, füllen, vollgießen, voll machen, English translation: "
    )
#"Q: An important UN summit took place when? Amswer:"
# "Q: What area of the world was less severely affected by the credit crunch according to The World Bank report In February 2009 in 3000 words? Answer:"
    llm = load_model(MODEL_PATH)
    if llm:
        print(f"\n{'='*60}\nRunning inference with max_tokens={args.max_tokens}\n{'='*60}")
        run_inference(llm, test_sequence, args.max_tokens)
