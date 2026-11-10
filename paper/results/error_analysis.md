# Error signatures and examples

These are automatically identified observations, not independently annotated causal explanations. Complete annotated support does not prove sufficient context, and an imperfect reference can affect F1. Cases are the first qualifying IDs in each frozen input order, rather than hand-picked winning examples.

## hotpotqa / qwen15

| Observation | Questions |
| --- | ---: |
| certified optimum with imperfect answer | 324 |
| complete annotated support with imperfect answer | 190 |
| correct answer without all annotated support | 24 |
| lower common energy but worse answer than relevance | 31 |

### certified optimum with imperfect answer

- `5a729cc25542991f9a20c532`: Which author wrote about a woman captured by the Symbionese Liberation Army? Reference: 'Paul Avery'. MILP: 'Susan Choi' (F1 0.0000); relevance: 'Susan Choi wrote about a woman captured by the Symbionese Liberation Army in her novel "American Woman".' (F1 0.0000). Same-objective energies: MILP -2.57623, relevance -2.49879.
- `5aba549f554299232ef4a290`: What kind of song did Alexander Grant produce for Eminem? Reference: 'a midtempo hip hop ballad'. MILP: 'Hip hop ballad' (F1 0.8571); relevance: 'Hip hop ballad' (F1 0.8571). Same-objective energies: MILP -1.83170, relevance -1.83170.

### complete annotated support with imperfect answer

- `5aba549f554299232ef4a290`: What kind of song did Alexander Grant produce for Eminem? Reference: 'a midtempo hip hop ballad'. MILP: 'Hip hop ballad' (F1 0.8571); relevance: 'Hip hop ballad' (F1 0.8571). Same-objective energies: MILP -1.83170, relevance -1.83170.
- `5ae25d2b554299495565da46`: Who has more singles titles, Brian Gottfried or Peter Fleming? Reference: '21'. MILP: 'Brian Gottfried has more singles titles than Peter Fleming.' (F1 0.0000); relevance: 'Peter Fleming' (F1 0.0000). Same-objective energies: MILP -1.66206, relevance -1.54111.

### correct answer without all annotated support

- `5add2ba55542994ed6169ca8`: What college did the English conductor, organist and composer widely regarded as Britain's leading conductor of choral works teach at? Reference: 'Royal College of Music'. MILP: 'Royal College of Music' (F1 1.0000); relevance: 'Royal College of Music' (F1 1.0000). Same-objective energies: MILP -2.02323, relevance -1.83409.
- `5a832a625542990548d0b1b4`: What airport is off National Route A002 and is largest airport in Greater Buenos Aires? Reference: 'Ministro Pistarini International Airport'. MILP: 'Ministro Pistarini International Airport' (F1 1.0000); relevance: 'Ministro Pistarini International Airport' (F1 1.0000). Same-objective energies: MILP -2.60907, relevance -2.47046.

### lower common energy but worse answer than relevance

- `5ab4071955429976abd1bd38`: How long was the career of the actor in The Skull? Reference: '70 years'. MILP: 'The career of the actor in The Skull lasted until 1965 when it was released.' (F1 0.0000); relevance: '7 years' (F1 0.5000). Same-objective energies: MILP -1.66659, relevance -1.56503.
- `5ae4585c5542996836b02c89`: Which band has more members Band of Skulls or Live ? Reference: 'Live'. MILP: 'Band of Skulls' (F1 0.0000); relevance: 'Live' (F1 1.0000). Same-objective energies: MILP -2.30368, relevance -2.25757.

## hotpotqa / qwen3

| Observation | Questions |
| --- | ---: |
| certified optimum with imperfect answer | 323 |
| complete annotated support with imperfect answer | 189 |
| lower common energy but worse answer than relevance | 37 |
| correct answer without all annotated support | 24 |

### certified optimum with imperfect answer

- `5a729cc25542991f9a20c532`: Which author wrote about a woman captured by the Symbionese Liberation Army? Reference: 'Paul Avery'. MILP: 'Susan Choi' (F1 0.0000); relevance: 'Susan Choi' (F1 0.0000). Same-objective energies: MILP -2.57623, relevance -2.49879.
- `5aba549f554299232ef4a290`: What kind of song did Alexander Grant produce for Eminem? Reference: 'a midtempo hip hop ballad'. MILP: 'hip hop ballad' (F1 0.8571); relevance: 'hip hop ballad' (F1 0.8571). Same-objective energies: MILP -1.83170, relevance -1.83170.

### complete annotated support with imperfect answer

- `5aba549f554299232ef4a290`: What kind of song did Alexander Grant produce for Eminem? Reference: 'a midtempo hip hop ballad'. MILP: 'hip hop ballad' (F1 0.8571); relevance: 'hip hop ballad' (F1 0.8571). Same-objective energies: MILP -1.83170, relevance -1.83170.
- `5ae25d2b554299495565da46`: Who has more singles titles, Brian Gottfried or Peter Fleming? Reference: '21'. MILP: 'Brian Gottfried' (F1 0.0000); relevance: 'Peter Fleming' (F1 0.0000). Same-objective energies: MILP -1.66206, relevance -1.54111.

### lower common energy but worse answer than relevance

- `5a88a8f4554299206df2b320`: Which battle took place closer to New York City, Battle of Fredericksburg or the Western Allied invasion of Germany ? Reference: 'Battle of Fredericksburg'. MILP: 'Western Allied invasion of Germany' (F1 0.2500); relevance: 'Battle of Fredericksburg' (F1 1.0000). Same-objective energies: MILP -1.89414, relevance -1.82605.
- `5adbd1d25542994650320bf6`: What is the current job of the former partner in ice skating of Vladimir Fedorov? Reference: 'She currently works as a coach and choreographer'. MILP: 'coach' (F1 0.2500); relevance: 'coach and choreographer' (F1 0.6000). Same-objective energies: MILP -1.84387, relevance -1.83459.

### correct answer without all annotated support

- `5adf72095542992d7e9f935d`: The New York, Westchester and Boston Railway has a terminus at the New York city in what county? Reference: 'Westchester'. MILP: 'Westchester' (F1 1.0000); relevance: 'Westchester' (F1 1.0000). Same-objective energies: MILP -3.03972, relevance -2.92936.
- `5a81b99c5542995ce29dcc56`: Atlas Shrugged was a film based on the books by a proponent of what philosophy? Reference: 'Objectivism'. MILP: 'Objectivism' (F1 1.0000); relevance: 'Objectivism' (F1 1.0000). Same-objective energies: MILP -2.79934, relevance -2.66845.

## musique / qwen15

| Observation | Questions |
| --- | ---: |
| certified optimum with imperfect answer | 413 |
| correct answer without all annotated support | 41 |
| lower common energy but worse answer than relevance | 36 |
| complete annotated support with imperfect answer | 96 |

### certified optimum with imperfect answer

- `4hop1__88342_75218_128008_46748`: The MLB MVP award is given out after a competition where a team has played the most games. What is the longest win streak in the history of league that team plays for? Reference: '26'. MILP: 'Chicago Cubs' (F1 0.0000); relevance: 'Chicago Cubs' (F1 0.0000). Same-objective energies: MILP -2.20641, relevance -2.12899.
- `2hop__85596_807969`: What team is the highest goal scorer in the EPL a member of? Reference: 'Egypt national football team'. MILP: 'Manchester City' (F1 0.0000); relevance: 'Manchester City' (F1 0.0000). Same-objective energies: MILP -1.90738, relevance -1.58546.

### correct answer without all annotated support

- `4hop3__160230_470287_345497_72134`: When did the death city of Taito Kantonen become the capital of the US state having the statue being the title of the various Latin Mother goddess? Reference: '1839'. MILP: '1839' (F1 1.0000); relevance: 'Noanswer' (F1 0.0000). Same-objective energies: MILP -1.39633, relevance -1.34817.
- `4hop3__827497_354093_254885_76356`: The Pee Dee River leads to a bay which leads to an ocean. Who led an attempt to link that ocean with the Pacific via a canal through the continental region containing the El Valle volcano? Reference: 'Ferdinand de Lesseps'. MILP: 'Ferdinand de Lesseps' (F1 1.0000); relevance: 'Ferdinand de Lesseps' (F1 1.0000). Same-objective energies: MILP -1.38335, relevance -1.29370.

### lower common energy but worse answer than relevance

- `4hop1__131611_32392_823060_610794`: In which county is the city sharing a border with the capitol of the state where Ocean Forest Country Club is located? Reference: 'Richland County'. MILP: 'Horry County' (F1 0.5000); relevance: 'Richland County' (F1 1.0000). Same-objective energies: MILP -1.86649, relevance -1.83101.
- `3hop1__321720_650651_7262`: Who was a prominent figure at the radio division of the network that created the version of The Biggest Loser set in the country where Seria is? Reference: 'Walter Sabo'. MILP: 'David Simon' (F1 0.0000); relevance: 'Walter Sabo' (F1 1.0000). Same-objective energies: MILP -1.54585, relevance -1.42331.

### complete annotated support with imperfect answer

- `2hop__345_59409`: Who was the person who purchased Tidal's parent company in 2015 talking about in the song 'Cry?' Reference: 'three different relationships he had in the past'. MILP: 'Jay-Z' (F1 0.0000); relevance: 'Jay-Z' (F1 0.0000). Same-objective energies: MILP -1.81547, relevance -1.72861.
- `3hop1__857_846_7701`: When did the city where the Yongle emperor greeted the person to whom the edict was addressed become the Chinese national capital? Reference: 'Jin dynasty'. MILP: '1407' (F1 0.0000); relevance: 'Noanswer' (F1 0.0000). Same-objective energies: MILP -1.79722, relevance -1.49621.

## musique / qwen3

| Observation | Questions |
| --- | ---: |
| certified optimum with imperfect answer | 445 |
| complete annotated support with imperfect answer | 105 |
| correct answer without all annotated support | 18 |
| lower common energy but worse answer than relevance | 32 |

### certified optimum with imperfect answer

- `4hop1__88342_75218_128008_46748`: The MLB MVP award is given out after a competition where a team has played the most games. What is the longest win streak in the history of league that team plays for? Reference: '26'. MILP: 'Noanswer' (F1 0.0000); relevance: 'noanswer' (F1 0.0000). Same-objective energies: MILP -2.20641, relevance -2.12899.
- `2hop__85596_807969`: What team is the highest goal scorer in the EPL a member of? Reference: 'Egypt national football team'. MILP: 'Tottenham Hotspur' (F1 0.0000); relevance: 'Liverpool' (F1 0.0000). Same-objective energies: MILP -1.90738, relevance -1.58546.

### complete annotated support with imperfect answer

- `2hop__91248_84207`: Who was the last soldier of the conflict that saw the government getting involved in healthcare to die? Reference: 'Albert Henry Woolson'. MILP: 'Bertie Felstead' (F1 0.0000); relevance: 'Bertie Felstead' (F1 0.0000). Same-objective energies: MILP -1.69433, relevance -1.69433.
- `2hop__345_59409`: Who was the person who purchased Tidal's parent company in 2015 talking about in the song 'Cry?' Reference: 'three different relationships he had in the past'. MILP: 'Jay-Z' (F1 0.0000); relevance: 'Jay-Z' (F1 0.0000). Same-objective energies: MILP -1.81547, relevance -1.72861.

### correct answer without all annotated support

- `3hop1__46571_87694_124169`: When did the Governor of the city where the Basilica named after the saint holding the knife in the Last Supper is located in end? Reference: '1952'. MILP: '1952' (F1 1.0000); relevance: 'noanswer' (F1 0.0000). Same-objective energies: MILP -1.83484, relevance -1.66116.
- `3hop1__622497_160088_49779`: Who is the host of Who Wants to be a Millionaire in the country that the producer of The Wild Women of Chastity Gulch is from? Reference: 'Chris Harrison'. MILP: 'Chris Harrison' (F1 1.0000); relevance: 'Chris Harrison' (F1 1.0000). Same-objective energies: MILP -1.91485, relevance -1.82547.

### lower common energy but worse answer than relevance

- `4hop1__131611_32392_823060_610794`: In which county is the city sharing a border with the capitol of the state where Ocean Forest Country Club is located? Reference: 'Richland County'. MILP: 'Horry' (F1 0.0000); relevance: 'Richland' (F1 0.6667). Same-objective energies: MILP -1.86649, relevance -1.83101.
- `2hop__132954_533882`: What company was formed after a merger of the company that built ASM-N-5 Gorgon V? Reference: 'Martin Marietta'. MILP: 'Lockheed Martin' (F1 0.5000); relevance: 'Martin Marietta' (F1 1.0000). Same-objective energies: MILP -1.59213, relevance -1.41872.

