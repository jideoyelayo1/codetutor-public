"""Apply verified web references to the original seed curriculum."""
import json
from pathlib import Path
def web(title,url,section,note=None): return dict(title=title,url=url,section=section,note=note)
CPP_PLAYLIST = 'https://www.youtube.com/playlist?list=PLfVsf4Bjg79AxxmZwARAh3J9SHNGarty8'
HAYDEN_CPP_PLAYLIST = 'https://www.youtube.com/playlist?list=PLi2pCZz5m6GEEDq-vt0cean5t638kb7_7'

def video(topic,seconds,timestamp): return web('Rust video course',f'https://www.youtube.com/watch?v=BpPEoZW5IiY&t={seconds}s',f'{topic} · {timestamp}','freeCodeCamp.org / Arfan Zubi (2023). Pair this chapter with current Rust documentation.')
READINGS={
 'cpp.raii':[web('C++ exceptions · LearningLad','https://www.youtube.com/watch?v=P_Kx0i7yXhU&list=PLfVsf4Bjg79AxxmZwARAh3J9SHNGarty8&index=10','try, catch, and throw · playlist video 10','Exception handling background. Use the lesson and Core Guidelines for destructor-driven cleanup.')],
 'cpp.move':[web('C++ copy construction · LearningLad','https://www.youtube.com/watch?v=2KvslbLHTUY&list=PLfVsf4Bjg79AxxmZwARAh3J9SHNGarty8&index=18&t=53s','Copy-constructor example · 00:53','Review copying before comparing it with moves.')],
 'rust.ownership':[web('The Rust Book','https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html','4.1 What Is Ownership?'),web('Rust by Example','https://doc.rust-lang.org/rust-by-example/scope/move.html','Ownership and moves'),video('Ownership',5573,'01:32:53'),],
 'rust.borrowing':[web('The Rust Book','https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html','4.2 References and Borrowing'),web('Rust by Example','https://doc.rust-lang.org/rust-by-example/scope/borrow.html','Borrowing'),video('Borrowing',8646,'02:24:06')],
 'rust.results':[web('The Rust Book','https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html','9.2 Recoverable Errors with Result'),web('Rust by Example','https://doc.rust-lang.org/rust-by-example/error/result.html','Result'),video('Result',35096,'09:44:56')],
 'lean.functions':[web('Functional Programming in Lean','https://lean-lang.org/functional_programming_in_lean/Getting-to-Know-Lean/','Chapter 1: Getting to Know Lean'),web('Lean learning hub','https://lean-lang.org/learn/','Official programmer-oriented learning resources')],
 'lean.proofs':[web('Theorem Proving in Lean 4','https://lean-lang.org/theorem_proving_in_lean4/Propositions-and-Proofs/','Chapter 3: Propositions and Proofs'),web('Functional Programming in Lean','https://lean-lang.org/functional_programming_in_lean/Interlude___-Propositions___-Proofs___-and-Indexing/','Interlude: Propositions, Proofs, and Indexing')],
 'lean.equality':[web('Theorem Proving in Lean 4','https://lean-lang.org/theorem_proving_in_lean4/Quantifiers-and-Equality/','Chapter 4: Quantifiers and Equality')],
}
READINGS['cpp.raii'].extend([
    web('Resource management · Hayden Smith','https://www.youtube.com/watch?v=p7nVL9qhFn4&list=PLi2pCZz5m6GEEDq-vt0cean5t638kb7_7&index=10','RAII and resource lifetime · lecture 10','Connect destructor-driven cleanup with copy control and moving owned resources.'),
    web('Smart pointers · Hayden Smith','https://www.youtube.com/watch?v=ZImvWF6sKoI&list=PLi2pCZz5m6GEEDq-vt0cean5t638kb7_7&index=11&t=151s','RAII with smart pointers · 02:31','Continue to exclusive, shared, and observing ownership models as needed.'),
])
READINGS['cpp.move'].append(
    web('Smart pointers · Hayden Smith','https://www.youtube.com/watch?v=ZImvWF6sKoI&list=PLi2pCZz5m6GEEDq-vt0cean5t638kb7_7&index=11&t=440s','Exclusive ownership · 07:20','Study unique_ptr ownership before running this lesson’s transfer example. For the precise role of std::move, use the lesson and current references.')
)

def apply(content):
    content['books']=[]
    for lesson in content['lessons']:
        lesson['reading']=READINGS.get(lesson['id'],[])
        if lesson['trackID'] in ['rust','lean'] and lesson['reading']: lesson['sourceURL']=lesson['reading'][0]['url']
    for card in content['cards']:
        card['sourceURL']=next(l['sourceURL'] for l in content['lessons'] if l['id']==card['lessonID'])
    for track in content['tracks']:
        if track['id']=='cpp' and not any(r['url']==HAYDEN_CPP_PLAYLIST for r in track['resources']): track['resources'].insert(1,dict(title='Hayden Smith · Advanced C++',url=HAYDEN_CPP_PLAYLIST,kind='Video course · COMP6771'))
        if track['id']=='cpp' and not any(r['url']==CPP_PLAYLIST for r in track['resources']): track['resources'].append(dict(title='LearningLad · C++ video refreshers',url=CPP_PLAYLIST,kind='Video playlist · updated 2015'))
        if track['id']=='lean' and not any(r['url']=='https://lean-lang.org/learn/' for r in track['resources']): track['resources'].insert(0,dict(title='Lean learning hub',url='https://lean-lang.org/learn/',kind='Learning hub'))
        if track['id']=='rust' and not any('BpPEoZW5IiY' in r['url'] for r in track['resources']): track['resources'].append(dict(title='Rust video course · freeCodeCamp / Arfan Zubi',url='https://www.youtube.com/watch?v=BpPEoZW5IiY',kind='Video'))
    return content
if __name__=='__main__':
    path=Path('CodingTeacher/curriculum.json');content=apply(json.loads(path.read_text()));path.write_text(json.dumps(content,indent=2,ensure_ascii=False)+'\n')
    print(f'{sum(len(l["reading"]) for l in content["lessons"])} lesson reading references')
