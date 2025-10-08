comandos_audios = {
    'holis':['holis'],
    'helldiver':['helldiver','helldivers','forsuperearth'],
    'cuervo':['cuervo'],
    'zazaraza':['zazaraza','indyforever','indy'],
    'piripipi':['piripipi','gg'],
    'dark':['dark'],
    'quiereme':['quiereme'],
    'sacrilegioso':['sacrilegioso','homero'],
    'sadsong':['sadsong','sad'],
    'boca':['bostero','boque'],
    'yeahbaby':['yeahbaby','yeababy','baby','larry','marit','marit887'],
    'wansaia82':['wansaia82','ariel','wansaia'],
    'presta':['red','presta','redfallen','theredfallen'],
    'distinta':['distinta','ella'],
    'sega':['sega','segaa','segaaa','segaaaa','segaaaaa'],
    'play':['sony','play','playstation'],
    'mario':['mario','nintendo','gameover'],
    'zelda':['zelda','link','item'],
    'alert':['alerta','alert','snake','metalgear','kojima'],
    'ernesto':['ernesto','tenembaum'],
    'yamete':['yamete','yametekudasai','kudasai','horny','hentai','anime'],
}

comandos_mensajes = {
    'boca':["boooooca booooooca","boca boca booooooca","booooooca boca boca"],
    'presta':["🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈"],
    'yamete':["yametekudasaaaaaaaai"],
}

autores_exclusivos = {
    'marit887':['yeahbaby'],
    'theredfallen':['presta'],
    'roque04_':['sega'],
}

comandos_general = [item for sublista in comandos_audios.values() for item in sublista] + list(comandos_mensajes.keys())
