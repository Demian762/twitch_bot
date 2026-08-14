comandos_audios = {
    'holis':['holis','holi'],
    'helldiver':['helldiver','helldivers','forsuperearth'],
    'cuervo':['cuervo'],
    'zazaraza':['zazaraza','indyforever','indy'],
    'piripipi':['piripipi','gg'],
    'dark':['dark'],
    'quiereme':['quiereme'],
    'sacrilegioso':['sacrilegioso','homero'],
    'sadsong':['sadsong','sad'],
    'boca':['boca','bostero','boque'],
    'yeahbaby':['yeahbaby','yeababy','baby','larry','marit','marit887'],
    'wansaia82':['wansaia82','ariel','wansaia'],
    'presta':['red','presta','redfallen','theredfallen'],
    'distinta':['distinta','ella'],
    'sega':['sega','segaa','segaaa','segaaaa','segaaaaa'],
    'play':['sony','play','playstation'],
    'mario':['mario','nintendo','gameover'],
    'zelda':['zelda','link','item'],
    'alert':['alerta','alert','metalgear','kojima'],
    'ernesto':['ernesto','tenembaum'],
    'yamete':['yamete','yametekudasai','kudasai','horny','hentai','anime'],
    'bija':['bija','capusotto'],
    'fumojuego':['fumo','lulu','fumojuego','fumoyjuego'],
    'repartidor':['repartidor','demian'],
    'emperor':['emperor','emperador','warhammer','titus'],
    'tose':['tose','norespira','heimlich','tos'],
    'emilio':['emilio','leon'],
    'saran':['saran','suspenso','jorge','zaran'],
    'win95':['win95','windows95'],
    'win98':['win98','windows98'],
    'allahu':['allahu','akbar','ala'],
    'arrugadito':['arrugadito','slurp'],
    'dross':['dross','poder'],
    'elisir':['elisir','coco','whisky'],
    'elpollodiablo':['elpollodiablo','pollodiablo'],
    'milk':['milk','leche'],
    'nodenuevo':['nodenuevo','decia','nodenuevodecia'],
    'snake':['snake'],
    'gatito':['gatito','gato','miau'],
    'dificil':['dificil','diablos'],
    'suatencion':['suatencion'],
    'coronacion':['coronacion','gloria'],
    'sierra':['sierra'],
    'aiseigudbai':['aiseigudbai'],
    'endai':['endai'],
    'peron':['peron'],
}

comandos_mensajes = {
    'boca':["boooooca booooooca","boca boca booooooca","booooooca boca boca"],
    'presta':["GayPride GayPride GayPride GayPride GayPride GayPride GayPride"],
    'yamete':["yametekudasaaaaaaaai"],
}

# Overrides de comandos_mensajes cuando corre en Kick, para las entradas que
# usan emotes específicos de Twitch (que en Kick aparecerían como texto
# literal). Si una clave no está acá, se usa la de comandos_mensajes de siempre.
comandos_mensajes_kick = {
    'presta':["ppJedi ppJedi ppJedi ppJedi ppJedi ppJedi ppJedi"],
    'yamete':["SenpaiWhoo SenpaiWhoo SenpaiWhoo SenpaiWhoo SenpaiWhoo"],
}

autores_exclusivos = {
    'marit887':['yeahbaby'],
    'theredfallen':['presta'],
    'roque04_':['sega'],
}

comandos_general = list(dict.fromkeys([item for sublista in comandos_audios.values() for item in sublista] + list(comandos_mensajes.keys())))
