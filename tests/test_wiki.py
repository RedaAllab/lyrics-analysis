import pandas as pd

from beatles_viz.credits import agreement_summary, compare_sources, lead_vocal_conflicts, musician_claims
from beatles_viz.wiki import cited_sentences, citation, personnel, personnel_section, split_roles

PAGE = """Intro.{{sfn|Smith|1999|p=4}}

==Recording==
Text.

==Personnel==
According to Ann Author:{{sfn|Author|2001|p=320}}

'''The Beatles'''
* [[John Lennon]]&nbsp;– lead, harmony and backing vocals; rhythm and acoustic guitars; [[piano]] on "Song A" and "Song B"
* [[Ringo Starr]] – drums; lead vocals {{small|("Song C")}}; hand claps{{sfn|Other|2010|pp=5–6}}

'''Additional musicians'''
* [[George Martin]] – production; harmonium (on "Song A")
* Robert Photo – photography

==Charts==
* not a credit – none
"""


def test_citation_and_section():
    assert citation("Everett|2001|p=320") == "Everett 2001, p. 320"
    assert citation("Guesdon|Margotin|2013|pp=277") == "Guesdon, Margotin 2013, pp. 277"
    section = personnel_section(PAGE)
    assert "Ringo Starr" in section and "Charts" not in section and "Recording" not in section
    assert personnel_section("== Background ==\ntext") == ""


def test_split_roles_shares_head_nouns_and_keeps_songs():
    roles = split_roles('lead, harmony and backing vocals; rhythm and acoustic guitars; piano on "A" and "B"')
    assert roles == [("lead vocal", []), ("harmony vocal", []), ("backing vocal", []), ("rhythm guitar", []),
                     ("acoustic guitar", []), ("piano", ["A", "B"])]
    assert split_roles('lead vocals (on "X", "Y", and "Z")') == [("lead vocal", ["X", "Y", "Z"])]


def test_personnel_rows():
    rows = pd.DataFrame(personnel(personnel_section(PAGE)))
    assert set(rows.person) == {"John Lennon", "Ringo Starr", "George Martin", "Robert Photo"}
    assert (rows.cited == "Author 2001, p. 320").all()
    lennon = rows[rows.person == "John Lennon"]
    assert lennon.kind.tolist() == ["lead_vocal", "backing_vocal", "backing_vocal", "instrument", "instrument",
                                    "instrument"]
    starr = rows[rows.person == "Ringo Starr"].set_index("role_text")
    assert starr.loc["lead vocal", "songs"] == ["Song C"] and starr.loc["drums", "family"] == "Percussion"
    assert starr.loc["hand claps", "family"] == "Percussion" and starr.loc["hand claps", "line_cited"] == "Other 2010, pp. 5–6"
    martin = rows[rows.person == "George Martin"].set_index("role_text")
    assert martin.loc["production", "kind"] == "producer" and martin.loc["harmonium", "songs"] == ["Song A"]
    assert rows[rows.person == "Robert Photo"].kind.tolist() == ["other"]


def test_cited_sentences():
    text = ("Lead text. ==Writing==\n"
            "Lennon wrote the verses.{{sfn|Author|2001|p=10}} The weather was fine. "
            'McCartney added the middle eight.<ref name="b">{{cite book |last=Writer |year=1997 |page=55}}</ref>\n'
            "==Personnel==\n* John Lennon wrote nothing here – vocals\n")
    rows = cited_sentences(text.replace("==Writing==", "\n==Writing=="))
    assert [r["cited"] for r in rows] == ["Author 2001, p. 10", "Writer 1997, p. 55"]
    assert rows[0]["section"] == "Writing" and "weather" not in " ".join(r["sentence"] for r in rows)


def test_compare_sources():
    perf = pd.DataFrame([
        ("A", "lennon", "lead_vocal", "", "mb"), ("A", "lennon", "instrument", "electric guitar", "mb"),
        ("A", "starr", "instrument", "drums (drum set)", "mb"),
        ("A", "lennon", "vocal", "", "wp"), ("A", "lennon", "instrument", "rhythm guitar", "wp"),
        ("A", "starr", "instrument", "drums", "wp"), ("A", "george_martin", "instrument", "piano", "wp"),
        ("B", "harrison", "lead_vocal", "", "mb"), ("C", "starr", "lead_vocal", "", "wp")],
        columns=["title", "person_id", "role", "detail", "source_id"])
    claims = musician_claims(perf, "wp")
    assert ("A", "lennon", "lead vocal") in set(map(tuple, claims.values))  # unqualified vocal, no other lead
    cmp = compare_sources(perf, "mb", "wp")
    assert set(cmp.title) == {"A"}
    diff = cmp[cmp.in_a != cmp.in_b]
    assert diff[["person_id", "aspect", "in_a", "in_b"]].values.tolist() == [["george_martin", "Keyboards", False, True]]
    s = agreement_summary(cmp).set_index("aspect")
    assert s.loc["Keyboards", "only_b"] == 1 and s.loc["Guitar", "agreed"] == 1.0
    assert compare_sources(perf, "mb", "wp", partial_b=True).in_b.all()


def test_lead_vocal_conflicts_with_three_sources():
    perf = pd.DataFrame([("A", "lennon", "lead_vocal", "list"), ("A", "lennon", "lead_vocal", "mb"),
                         ("A", "mccartney", "lead_vocal", "wp"), ("B", "starr", "lead_vocal", "list"),
                         ("B", "starr", "lead_vocal", "mb")], columns=["title", "person_id", "role", "source_id"])
    c = lead_vocal_conflicts(perf)
    assert c.title.tolist() == ["A"] and c.iloc[0]["wp"] == "mccartney"
    assert lead_vocal_conflicts(perf, ["list", "mb"]).empty


def test_authorship_summary_flags_differing_accounts():
    from beatles_viz.credits import authorship_summary
    work = pd.DataFrame([
        ("A", "lennon", "credited_writer", "official", ""), ("A", "lennon", "main_writer", "documented", ""),
        ("A", "mccartney", "middle_eight", "documented", ""),
        ("B", "lennon", "middle_eight", "documented", ""), ("B", "mccartney", "middle_eight", "documented", ""),
        ("C", "lennon", "sole_writer", "documented", ""), ("C", "mccartney", "co_writer", "documented", ""),
        ("D", "mccartney", "main_writer", "documented", "authorship disputed")],
        columns=["title", "person_id", "role", "kind", "detail"])
    s = authorship_summary(work).set_index("title")
    assert s.loc["A", "main"] == "Lennon" and s.loc["A", "parts"] == "Mccartney" and not s.loc["A", "accounts_differ"]
    assert s.loc[["B", "C", "D"], "accounts_differ"].all()
    assert s.loc["A", "claims"] == 2  # the official credit is not a claim


def test_references_with_a_slash_in_their_name():
    line = ('* [[George Harrison]] – harmony vocals,<ref name="Web/About" /> rhythm guitar,{{sfn|Lewisohn|2005|p=152}} '
            'handclaps\n* [[Ringo Starr]] – drums<ref name="x">{{cite book |last=Smith |year=1990 |page=3}}</ref>')
    rows = pd.DataFrame(personnel(line))
    assert rows[rows.person == "George Harrison"].role_text.tolist() == ["harmony vocal", "rhythm guitar", "handclaps"]
    assert rows[rows.person == "Ringo Starr"].role_text.tolist() == ["drums"]


def test_shared_head_only_where_it_fits():
    assert [r for r, _ in split_roles("bass, backing vocals")] == ["bass", "backing vocal"]
    assert [r for r, _ in split_roles("piano, bass, drums")] == ["piano", "bass", "drums"]
    assert [r for r, _ in split_roles("bass and lead guitars")] == ["bass guitar", "lead guitar"]
