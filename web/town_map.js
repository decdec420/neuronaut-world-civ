/*
 * Town map: the world drawn as a top-down 2D village.
 *
 * Everything here is drawn in code (no image files): the real terrain from
 * GET /map, buildings where they actually stand (by kind: cottage, barn,
 * workshop, temple, school, market...), the agents' roads, wells and street
 * lamps, and every agent as a small pixel-art character with its own look,
 * walking animation and a bubble showing what it is doing. At night lamps,
 * lit windows and bonfires light the dark.
 *
 * Usage (web/enhanced.html):
 *   TownMap.init(canvas)              once
 *   TownMap.update(snapshot)          on every websocket snapshot
 *   TownMap.render(ctx, snapshot, fn) every frame; fn(ctx) draws extra
 *                                     things in world pixels (particles...)
 *   TownMap.worldPx(location)         {x, y} in world pixels, for effects
 *   TownMap.hoveredAgent()            the agent under the mouse, if any
 *
 * Controls: drag to pan, wheel to zoom, click a character to follow it,
 * click the minimap to jump there, buttons for zoom / follow village / map.
 */
(function () {
    'use strict';

    const TILE = 16;                 // world pixels per map tile
    const SPRITE_W = 12, SPRITE_H = 18;

    // ---------------------------------------------------------------- utils
    function hash(str) {
        let h = 2166136261;
        for (let i = 0; i < str.length; i++) {
            h ^= str.charCodeAt(i);
            h = Math.imul(h, 16777619);
        }
        return h >>> 0;
    }
    function rng(seed) {             // mulberry32
        let a = seed >>> 0;
        return function () {
            a = (a + 0x6D2B79F5) >>> 0;
            let t = a;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }
    function pick(list, n) { return list[n % list.length]; }
    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
    function shade(hex, amt) {
        const n = parseInt(hex.slice(1), 16);
        let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
        const f = amt < 0 ? 0 : 255, p = Math.abs(amt);
        r = Math.round((f - r) * p + r); g = Math.round((f - g) * p + g); b = Math.round((f - b) * p + b);
        return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }
    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, c =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    // ------------------------------------------------------------- palettes
    const SKIN = ['#f6d5b8', '#eac09a', '#d9a273', '#b97f50', '#8d5a3a', '#5e3b26'];
    const HAIR = ['#2b1d14', '#4a2f1c', '#7a4a24', '#b07a3c', '#d9b45a', '#1d1d2b', '#a23b2a', '#6b6b78'];
    const SHIRT = ['#e05252', '#3f7fd9', '#46a35a', '#e0a33a', '#8e5cc9', '#2fb5b0', '#e07ab3', '#5c6b7a', '#c9683a', '#efeee4'];
    const PANTS = ['#3a4a6b', '#4b3a2b', '#2f2f38', '#5a6b3a', '#6b4a6b', '#7a6a55'];
    const HATS = ['#c0392b', '#2d6cb5', '#d9a441', '#3d8a4a', '#6b4a8a'];
    const ROOFS = ['#b5473a', '#3f6fb5', '#5b8f4a', '#8a5a3c', '#6b6b78', '#a8743a'];
    const WALLS = ['#e2cfa8', '#d4b68a', '#ebe3d3', '#c99a6b', '#d9c7b0'];

    const ACTIONS = {
        gather_food: ['🍎', 'gathering food'], gather_water: ['💧', 'fetching water'],
        drink: ['🥤', 'drinking'], eat: ['🍲', 'eating'], rest: ['💤', 'resting'],
        socialize: ['💬', 'chatting'], tell_story: ['📖', 'telling a story'], teach: ['🧑‍🏫', 'teaching'],
        learn: ['📚', 'learning'], build: ['🔨', 'building'], build_house: ['🏠', 'building a house'],
        gather_materials: ['🪵', 'gathering materials'], explore: ['🧭', 'exploring'],
        experiment: ['⚗️', 'experimenting'], refine: ['🔥', 'refining'], craft: ['🛠️', 'crafting'],
        create_art: ['🎨', 'making art'], trade: ['🤝', 'trading'], govern: ['🏛️', 'governing'],
        vote: ['🗳️', 'voting'], make_law: ['📜', 'proposing a law'], worship: ['🙏', 'worshipping'],
        pray: ['🙏', 'praying'], perform_ritual: ['🕯️', 'holding a ritual'],
        seek_romance: ['💕', 'courting'], try_for_child: ['💞', 'hoping for a child'],
        care_for_child: ['🍼', 'caring for a child'], hunt: ['🏹', 'hunting'], fish: ['🎣', 'fishing'],
        farm: ['🌱', 'farming'], plant_seeds: ['🌱', 'planting'], harvest: ['🌾', 'harvesting'],
        heal: ['🩹', 'healing'], attend_event: ['🎉', 'going to a gathering'],
        organize_event: ['📣', 'inviting everyone'], build_road: ['🛣️', 'paving a road'],
        dig_well: ['🪣', 'digging a well'], build_streetlight: ['🏮', 'putting up a lamp'],
        play_game: ['🎲', 'playing a game'], gamble: ['🎲', 'gambling'], mint_coins: ['🪙', 'minting coins'],
        fight: ['⚔️', 'fighting'], steal: ['🫳', 'stealing'], meditate: ['🧘', 'meditating'],
        write: ['✍️', 'writing'], discover_material: ['🔍', 'researching'], invent: ['💡', 'inventing'],
        hide: ['🛖', 'taking shelter'], idle: ['🤔', 'thinking'],
    };
    function actionInfo(name) {
        if (!name) return ACTIONS.idle;
        return ACTIONS[name] || ['⚙️', name.replace(/_/g, ' ')];
    }

    // ---------------------------------------------------------- characters
    // 10x16 templates (outlined to 12x18). H hair, S skin, E eye, T shirt,
    // B belt, P trousers, F shoes, C hat.
    const BODY_FRONT = ['.TTTTTTTT.', 'TTTTTTTTTT', 'TTTTTTTTTT', 'S.TTTTTT.S', '..BBBBBB..'];
    const LEGS_FRONT = [
        ['..PPPPPP..', '..PP..PP..', '..PP..PP..', '..FF..FF..'],
        ['..PPPPPP..', '..PP..PP..', '..PP..FF..', '..FF......'],
        ['..PPPPPP..', '..PP..PP..', '..FF..PP..', '......FF..'],
    ];
    const BODY_SIDE = ['...TTTT...', '..TTTTTT..', '..TTTTTT..', '...TSTT...', '...BBBB...'];
    const LEGS_SIDE = [
        ['...PPPP...', '...PPPP...', '...PPPP...', '...FFFFF..'],
        ['...PPPP...', '..PP..PP..', '.PP....PP.', '.FF....FFF'],
        ['...PPPP...', '...PPPP...', '...PPPP...', '...FFFFF..'],
    ];
    const HEADS = {
        down: ['..HHHHHH..', '.HHHHHHHH.', '.HHSSSSHH.', '.HSSSSSSH.', '.SSESSESS.', '..SSSSSS..', '...SSSS...'],
        up: ['..HHHHHH..', '.HHHHHHHH.', '.HHHHHHHH.', '.HHHHHHHH.', '.HHHHHHHH.', '..HHHHHH..', '...SSSS...'],
        right: ['..HHHHH...', '.HHHHHHH..', '.HHHHSSSS.', '.HHHSSSSS.', '.HHSSSSES.', '..HSSSSSS.', '...SSSS...'],
    };

    function setCell(rows, r, c, ch) {
        if (r < 0 || r >= rows.length || c < 0 || c >= rows[r].length) return;
        rows[r] = rows[r].slice(0, c) + ch + rows[r].slice(c + 1);
    }

    function template(dir, frame, style) {
        const side = dir === 'left' || dir === 'right';
        const head = HEADS[side ? 'right' : dir].slice();
        const body = (side ? BODY_SIDE : BODY_FRONT).slice();
        const legs = (side ? LEGS_SIDE : LEGS_FRONT)[frame].slice();
        const rows = head.concat(body, legs);
        if (style === 1) {               // long hair
            if (dir === 'down') {
                [4, 5].forEach(r => { setCell(rows, r, 1, 'H'); setCell(rows, r, 8, 'H'); });
                [6, 7].forEach(r => { setCell(rows, r, 1, 'H'); setCell(rows, r, 2, 'H'); setCell(rows, r, 7, 'H'); setCell(rows, r, 8, 'H'); });
            } else if (dir === 'up') {
                rows[5] = '.HHHHHHHH.'; rows[6] = '.HHHHHHHH.'; rows[7] = '.HHHHHHHH.';
            } else {
                [5, 6, 7].forEach(r => { setCell(rows, r, 1, 'H'); setCell(rows, r, 2, 'H'); });
            }
        } else if (style === 2) {        // hat
            rows[0] = rows[0].replace(/H/g, 'C');
            rows[1] = rows[1].replace(/H/g, 'C');
            rows[2] = side ? '.CCCCCCCCC' : 'CCCCCCCCCC';
        } else if (style === 3) {        // close-cropped
            rows[0] = '..........';
            if (dir === 'down') rows[2] = '.HSSSSSSH.';
        }
        if (dir === 'left') return rows.map(r => r.split('').reverse().join(''));
        return rows;
    }

    const spriteCache = new Map();
    function lookFor(agent) {
        const h = hash(agent.id || agent.name || '?');
        const elder = agent.life_stage === 'elder';
        return {
            key: `${h}|${elder ? 1 : 0}`,
            skin: pick(SKIN, h >>> 3),
            hair: elder ? pick(['#d8d8d8', '#bdbdbd', '#efefef'], h >>> 7) : pick(HAIR, h >>> 7),
            shirt: pick(SHIRT, h >>> 11),
            pants: pick(PANTS, h >>> 15),
            hat: pick(HATS, h >>> 19),
            style: (h >>> 22) % 4,
        };
    }

    function sprite(look, dir, frame) {
        const key = `${look.key}|${dir}|${frame}`;
        let c = spriteCache.get(key);
        if (c) return c;
        const rows = template(dir, frame, look.style);
        c = document.createElement('canvas');
        c.width = SPRITE_W; c.height = SPRITE_H;
        const g = c.getContext('2d');
        const colors = {
            H: look.hair, S: look.skin, E: '#231a1a', T: look.shirt, B: shade(look.pants, -0.35),
            P: look.pants, F: '#3b2a20', C: look.hat,
        };
        rows.forEach((row, y) => {
            for (let x = 0; x < row.length; x++) {
                const ch = row[x];
                if (ch === '.') continue;
                g.fillStyle = colors[ch] || '#ff00ff';
                g.fillRect(x + 1, y + 1, 1, 1);
            }
        });
        // shirt shading on the lower body, then a dark outline round the figure
        const img = g.getImageData(0, 0, SPRITE_W, SPRITE_H);
        const d = img.data, solid = i => d[i * 4 + 3] > 0;
        const outline = [];
        for (let y = 0; y < SPRITE_H; y++) {
            for (let x = 0; x < SPRITE_W; x++) {
                const i = y * SPRITE_W + x;
                if (solid(i)) continue;
                const n = (x > 0 && solid(i - 1)) || (x < SPRITE_W - 1 && solid(i + 1)) ||
                          (y > 0 && solid(i - SPRITE_W)) || (y < SPRITE_H - 1 && solid(i + SPRITE_W));
                if (n) outline.push(i);
            }
        }
        outline.forEach(i => { d[i * 4] = 28; d[i * 4 + 1] = 22; d[i * 4 + 2] = 34; d[i * 4 + 3] = 220; });
        g.putImageData(img, 0, 0);
        spriteCache.set(key, c);
        return c;
    }

    // -------------------------------------------------------------- state
    const T = {
        canvas: null, dpr: 1, W: 0, H: 0,
        map: null, terrain: null, mini: null, mapTick: -1, loadingMap: false,
        water: [],                                  // water tiles for the shimmer
        roads: null, roadsKey: '',
        agents: new Map(),                          // id -> view state
        data: null, lastUpdate: 0, interval: 1000,
        cam: { x: 800, y: 800, zoom: 1 }, camTarget: null,
        mode: 'village',                            // 'village' | 'free' | 'agent'
        followId: null,
        mouse: { x: -1, y: -1, inside: false }, drag: null, dragged: false,
        hover: null, hoverBuilding: null,
        speech: new Map(), seenTalk: new Set(),
        lightCanvas: null, rain: [],
        controls: null, card: null,
        onProfile: null,
        frameMs: 0,
    };

    // ------------------------------------------------------------ terrain
    const GROUND = {
        p: ['#7cc35a', '#78bf56', '#82c860'],
        f: ['#5a9e47', '#559944', '#5fa44c'],
        m: ['#8d9098', '#878a93', '#93969e'],
        w: ['#3d8fd1', '#3a8acb', '#4195d6'],
        d: ['#e6cf8b', '#e2ca85', '#ead493'],
    };
    const MINI = { p: '#7cc35a', f: '#3f7f3a', m: '#8d9098', w: '#3d8fd1', d: '#e6cf8b' };

    function terrainAt(x, y) {
        const m = T.map;
        if (!m || x < 0 || y < 0 || x >= m.width || y >= m.height) return 'w';
        return m.terrain[y][x];
    }

    function drawTree(g, x, y, r, pine) {
        g.fillStyle = 'rgba(0,0,0,0.22)';
        g.beginPath(); g.ellipse(x, y + 1, 6 * r, 2.5 * r, 0, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#6b4426';
        g.fillRect(x - 1, y - 5 * r, 3, 5 * r + 1);
        if (pine) {
            const layers = [['#2e6b3a', 0], ['#3a8045', 4], ['#4b9452', 8]];
            layers.forEach(([c, o]) => {
                g.fillStyle = c;
                g.beginPath();
                g.moveTo(x - (7 - o / 2) * r, y - (4 + o) * r);
                g.lineTo(x + 0.5, y - (14 + o) * r);
                g.lineTo(x + 1 + (7 - o / 2) * r, y - (4 + o) * r);
                g.closePath(); g.fill();
            });
        } else {
            g.fillStyle = '#2f6b35';
            g.beginPath(); g.arc(x + 0.5, y - 9 * r, 7 * r, 0, Math.PI * 2); g.fill();
            g.fillStyle = '#3d8a3f';
            g.beginPath(); g.arc(x - 0.5, y - 10 * r, 5.5 * r, 0, Math.PI * 2); g.fill();
            g.fillStyle = '#5aa84f';
            g.beginPath(); g.arc(x - 2, y - 12 * r, 2.5 * r, 0, Math.PI * 2); g.fill();
        }
    }

    function buildTerrain(map) {
        const W = map.width * TILE, H = map.height * TILE;
        const c = document.createElement('canvas');
        c.width = W; c.height = H;
        const g = c.getContext('2d');
        const mini = document.createElement('canvas');
        mini.width = map.width; mini.height = map.height;
        const mg = mini.getContext('2d');
        T.water = [];
        const props = [];                     // trees, rocks, bushes: drawn after the ground, by y
        const resources = map.resources || {};
        const resAt = {};
        Object.keys(resources).forEach(kind => resources[kind].forEach(([x, y]) => { resAt[`${x},${y}`] = (resAt[`${x},${y}`] || '') + kind[0]; }));

        for (let y = 0; y < map.height; y++) {
            for (let x = 0; x < map.width; x++) {
                const t = map.terrain[y][x];
                const r = rng(hash(`${x},${y}`));
                const px = x * TILE, py = y * TILE;
                g.fillStyle = GROUND[t][Math.floor(r() * 3)];
                g.fillRect(px, py, TILE, TILE);
                mg.fillStyle = MINI[t]; mg.fillRect(x, y, 1, 1);
                const res = resAt[`${x},${y}`] || '';
                if (t === 'w') {
                    T.water.push([x, y]);
                    const deep = terrainAt(x - 2, y) === 'w' && terrainAt(x + 2, y) === 'w' && terrainAt(x, y - 2) === 'w' && terrainAt(x, y + 2) === 'w';
                    if (deep) { g.fillStyle = 'rgba(20,60,120,0.25)'; g.fillRect(px, py, TILE, TILE); }
                    for (let i = 0; i < 2; i++) {
                        g.fillStyle = 'rgba(160,215,245,0.5)';
                        g.fillRect(px + Math.floor(r() * 12), py + Math.floor(r() * 15), 3, 1);
                    }
                    continue;
                }
                // specks and tufts
                const specks = t === 'm' ? ['#6f737c', '#a5a8b0'] : t === 'd' ? ['#d2b770', '#f1dea6'] :
                    t === 'f' ? ['#4a8a3c', '#6db35a'] : ['#5ea944', '#95d470'];
                for (let i = 0; i < 7; i++) {
                    g.fillStyle = specks[i % 2];
                    g.fillRect(px + Math.floor(r() * 15), py + Math.floor(r() * 15), t === 'm' ? 2 : 1, t === 'p' || t === 'f' ? 2 : 1);
                }
                if (t === 'p' && r() < 0.07) {
                    g.fillStyle = pick(['#f4f1de', '#f2c14e', '#e07a9a', '#9b8cf2'], Math.floor(r() * 4));
                    const fx = px + 3 + Math.floor(r() * 10), fy = py + 3 + Math.floor(r() * 10);
                    g.fillRect(fx, fy, 2, 2);
                    g.fillStyle = '#f7e27a'; g.fillRect(fx, fy, 1, 1);
                }
                if (t === 'm') {
                    if (r() < 0.35 || res.includes('s')) props.push(['rock', px + 4 + r() * 8, py + 8 + r() * 6, 0.7 + r() * 0.6]);
                    if (r() < 0.25) { g.fillStyle = '#6f737c'; g.fillRect(px + Math.floor(r() * 10), py + Math.floor(r() * 12), 5, 1); }
                }
                if (t === 'd') {
                    if (r() < 0.04) props.push(['cactus', px + 8, py + 12, 1]);
                    if (r() < 0.2) { g.fillStyle = '#d6bd78'; g.fillRect(px + Math.floor(r() * 8), py + Math.floor(r() * 14), 7, 1); }
                }
                if (t === 'f' && (r() < 0.55 || res.includes('w'))) {
                    props.push(['tree', px + 4 + r() * 8, py + 10 + r() * 5, 0.8 + r() * 0.35, r() < 0.35]);
                }
                if (t === 'p' && r() < 0.04) props.push(['tree', px + 8, py + 13, 0.85, false]);
                if (res.includes('f') && (t === 'p' || t === 'f') && r() < 0.35) props.push(['bush', px + 4 + r() * 8, py + 9 + r() * 5, 1]);
            }
        }
        // beaches: sand on land edges that touch water
        for (let y = 0; y < map.height; y++) {
            for (let x = 0; x < map.width; x++) {
                if (map.terrain[y][x] === 'w') continue;
                const px = x * TILE, py = y * TILE;
                const edges = [[0, -1], [1, 0], [0, 1], [-1, 0]];
                edges.forEach(([dx, dy]) => {
                    if (terrainAt(x + dx, y + dy) !== 'w') return;
                    g.fillStyle = '#e9d9a2';
                    if (dy === -1) g.fillRect(px, py, TILE, 3);
                    if (dy === 1) g.fillRect(px, py + TILE - 3, TILE, 3);
                    if (dx === -1) g.fillRect(px, py, 3, TILE);
                    if (dx === 1) g.fillRect(px + TILE - 3, py, 3, TILE);
                    g.fillStyle = 'rgba(255,255,255,0.55)';   // foam on the water side
                    if (dy === -1) g.fillRect(px, py - 1, TILE, 1);
                    if (dy === 1) g.fillRect(px, py + TILE, TILE, 1);
                    if (dx === -1) g.fillRect(px - 1, py, 1, TILE);
                    if (dx === 1) g.fillRect(px + TILE, py, 1, TILE);
                });
            }
        }
        props.sort((a, b) => a[2] - b[2]);
        props.forEach(p => {
            const [kind, x, y, s, pine] = p;
            if (kind === 'tree') drawTree(g, x, y, s, pine);
            else if (kind === 'rock') {
                g.fillStyle = 'rgba(0,0,0,0.2)'; g.fillRect(x - 4 * s, y, 9 * s, 2);
                g.fillStyle = '#7b7f88'; g.beginPath(); g.ellipse(x, y - 2 * s, 4.5 * s, 3.5 * s, 0, 0, Math.PI * 2); g.fill();
                g.fillStyle = '#a3a7af'; g.beginPath(); g.ellipse(x - 1.2 * s, y - 3.2 * s, 2 * s, 1.5 * s, 0, 0, Math.PI * 2); g.fill();
            } else if (kind === 'bush') {
                g.fillStyle = 'rgba(0,0,0,0.2)'; g.fillRect(x - 4, y, 9, 2);
                g.fillStyle = '#3f8f3a'; g.beginPath(); g.arc(x, y - 3, 4.5, 0, Math.PI * 2); g.fill();
                g.fillStyle = '#d64545';
                [[-2, -4], [1, -2], [2, -5], [-1, -1]].forEach(([dx, dy]) => g.fillRect(x + dx, y + dy, 1.5, 1.5));
            } else if (kind === 'cactus') {
                g.fillStyle = '#4f8f43';
                g.fillRect(x - 1, y - 10, 3, 10); g.fillRect(x - 4, y - 7, 2, 4); g.fillRect(x - 4, y - 7, 3, 1);
                g.fillRect(x + 3, y - 8, 2, 3); g.fillRect(x + 2, y - 6, 3, 1);
            }
        });
        T.terrain = c;
        T.mini = mini;
    }

    function loadMap(tick) {
        if (T.loadingMap) return;
        T.loadingMap = true;
        fetch('/map').then(r => r.ok ? r.json() : Promise.reject(new Error(`/map ${r.status}`))).then(map => {
            T.map = map;
            T.mapTick = tick;
            buildTerrain(map);
            T.roadsKey = '';
            if (!T.camTarget) {
                T.cam.x = map.width * TILE / 2;
                T.cam.y = map.height * TILE / 2;
            }
        }).catch(err => console.warn('Town map: could not load /map', err))
          .finally(() => { T.loadingMap = false; });
    }

    // --------------------------------------------------------------- roads
    function buildRoads(roads) {
        const key = roads.length + ':' + (roads.length ? roads[roads.length - 1].join(',') : '');
        if (key === T.roadsKey && T.roads) return;
        T.roadsKey = key;
        if (!T.map) return;
        const c = T.roads || document.createElement('canvas');
        c.width = T.map.width * TILE; c.height = T.map.height * TILE;
        const g = c.getContext('2d');
        g.clearRect(0, 0, c.width, c.height);
        const set = new Set(roads.map(([x, y]) => `${x},${y}`));
        roads.forEach(([x, y]) => {
            const px = x * TILE, py = y * TILE;
            g.fillStyle = '#b9ad92';
            g.fillRect(px, py, TILE, TILE);
            const r = rng(hash(`road${x},${y}`));
            for (let i = 0; i < 6; i++) {           // cobbles
                const cx = px + 1 + Math.floor(r() * 11), cy = py + 1 + Math.floor(r() * 11);
                g.fillStyle = '#9e927a'; g.fillRect(cx, cy, 4, 3);
                g.fillStyle = '#d3c8ad'; g.fillRect(cx, cy, 3, 1);
            }
            g.fillStyle = '#857a63';
            if (!set.has(`${x},${y - 1}`)) g.fillRect(px, py, TILE, 1);
            if (!set.has(`${x},${y + 1}`)) g.fillRect(px, py + TILE - 1, TILE, 1);
            if (!set.has(`${x - 1},${y}`)) g.fillRect(px, py, 1, TILE);
            if (!set.has(`${x + 1},${y}`)) g.fillRect(px + TILE - 1, py, 1, TILE);
        });
        T.roads = c;
    }

    // ----------------------------------------------------------- buildings
    // What a building looks like follows what it was built for. Purposes seen
    // in runs: shelter, workshop, storage, gathering_space; the rest are the
    // BuildingPurpose values in world/dynamic_buildings.py.
    const KIND_BY_PURPOSE = [
        ['house', ['shelter', 'warmth']],
        ['workshop', ['workshop', 'crafting', 'manufacturing']],
        ['barn', ['storage', 'food_production']],
        ['temple', ['worship']],
        ['pavilion', ['gathering_space', 'gathering', 'entertainment']],
        ['market', ['trading', 'banking', 'trade', 'commerce']],
        ['school', ['education', 'knowledge']],
        ['tower', ['protection', 'surveillance']],
        ['dome', ['research', 'energy_generation', 'space_exploration']],
        ['shed', ['resource_extraction', 'transportation']],
    ];
    const KIND_BY_CATEGORY = {
        Religious: 'temple', Commerce: 'market', Education: 'school', Industrial: 'workshop',
        Recreation: 'pavilion', Defense: 'tower', Advanced: 'dome', Infrastructure: 'shed',
    };
    function buildingKind(b) {
        const p = b.purposes || [];
        for (const [kind, purposes] of KIND_BY_PURPOSE) if (purposes.some(x => p.includes(x))) return kind;
        return KIND_BY_CATEGORY[b.category] || 'house';
    }
    const SIZES = {   // width, wall height, roof height (world px)
        house: [30, 14, 12], barn: [34, 16, 12], temple: [38, 18, 12], market: [34, 12, 8],
        school: [38, 16, 11], workshop: [34, 14, 9], pavilion: [34, 10, 9], tower: [20, 30, 6],
        dome: [32, 14, 14], shed: [22, 11, 8],
    };

    function roofBlock(g, left, top, w, rh, color) {
        // a 3/4-view roof: lighter far slope, darker near slope, a ridge, shingles
        g.fillStyle = shade(color, 0.12); g.fillRect(left, top, w, Math.ceil(rh / 2));
        g.fillStyle = color; g.fillRect(left, top + Math.ceil(rh / 2), w, Math.floor(rh / 2));
        g.fillStyle = shade(color, -0.25);
        for (let y = top + 2; y < top + rh; y += 3) g.fillRect(left, y, w, 1);
        g.fillStyle = shade(color, 0.3); g.fillRect(left, top + Math.ceil(rh / 2) - 1, w, 1);
        g.fillStyle = shade(color, -0.45); g.fillRect(left, top + rh - 1, w, 1);
        g.fillStyle = 'rgba(28,22,34,0.85)';
        g.fillRect(left - 1, top, 1, rh); g.fillRect(left + w, top, 1, rh); g.fillRect(left, top - 1, w, 1);
    }

    function windowAt(g, x, y, lit, w = 5, h = 5) {
        g.fillStyle = '#4a3322'; g.fillRect(x - 1, y - 1, w + 2, h + 2);
        g.fillStyle = lit ? '#ffd66b' : '#3c5a7a'; g.fillRect(x, y, w, h);
        g.fillStyle = lit ? '#fff1b8' : '#6f8fb0'; g.fillRect(x, y, 2, 2);
        g.fillStyle = '#4a3322'; g.fillRect(x + Math.floor(w / 2), y, 1, h);
    }

    function drawBuilding(g, b, now, night, lights) {
        const kind = buildingKind(b);
        const [w, wh, rh] = SIZES[kind];
        const x = Math.round(b.x * TILE + TILE / 2), y = Math.round(b.y * TILE + TILE / 2 + 6);
        const left = x - Math.round(w / 2), top = y - wh;
        const h = hash(b.id);
        const roof = pick(ROOFS, h >>> 2), wall = pick(WALLS, h >>> 6);
        b._box = [left - 3, top - rh - 4, w + 6, wh + rh + 6];
        // ground shadow
        g.fillStyle = 'rgba(0,0,0,0.22)'; g.fillRect(left + 2, y - 1, w, 4);

        if (b.collapsed) {
            const r = rng(h);
            for (let i = 0; i < 9; i++) {
                g.fillStyle = pick(['#7d7468', '#958b7c', '#6b5a48', '#a39a8a'], i);
                g.fillRect(left + r() * (w - 6), y - 3 - r() * 8, 4 + r() * 6, 3 + r() * 3);
            }
            g.fillStyle = '#6b4426'; g.save(); g.translate(x, y - 6); g.rotate(-0.5); g.fillRect(-10, 0, 20, 2); g.restore();
            return;
        }
        if (!b.complete) {
            const p = clamp(b.progress || 0, 0, 1);
            g.fillStyle = '#9c7a55'; g.fillRect(left, y - 4, w, 4);                    // foundation
            const built = Math.round(wh * p);
            if (built > 0) { g.fillStyle = wall; g.fillRect(left, y - 4 - built, w, built); }
            g.fillStyle = '#7a5230';
            [left, left + w - 2, x - 1].forEach(px => g.fillRect(px, top - 2, 2, wh + 2));   // posts
            g.fillRect(left, top - 2, w, 2);
            g.fillStyle = 'rgba(122,82,48,0.8)';                                         // scaffold
            for (let i = 0; i < 3; i++) g.fillRect(left - 3, top + 2 + i * 5, w + 6, 1);
            g.fillStyle = '#222'; g.fillRect(left, y + 3, w, 3);
            g.fillStyle = '#f59e0b'; g.fillRect(left, y + 3, Math.round(w * p), 3);
            return;
        }
        const lit = night && b.home_now > 0;
        const wallTop = top;
        if (kind === 'market') {
            g.fillStyle = '#8a6040'; g.fillRect(left, y - 8, w, 8);                       // counter
            g.fillStyle = '#6b4426'; g.fillRect(left + 1, top - rh, 2, wh + rh); g.fillRect(left + w - 3, top - rh, 2, wh + rh);
            for (let i = 0; i < w; i += 4) {                                               // striped awning
                g.fillStyle = (i / 4) % 2 ? '#efeee4' : '#d94c4c';
                g.fillRect(left - 2 + i, top - rh, 4, rh);
                g.fillRect(left - 2 + i, top, 4, 2 + ((i / 4) % 2));
            }
            [['#e05252', 4], ['#f2c14e', 12], ['#7fbf4a', 20], ['#e0a33a', 27]].forEach(([c, dx]) => {
                g.fillStyle = '#7a5230'; g.fillRect(left + dx - 1, y - 11, 6, 3);
                g.fillStyle = c; g.fillRect(left + dx, y - 12, 4, 2);
            });
            return;
        }
        if (kind === 'pavilion') {
            g.fillStyle = '#9c7a55'; g.fillRect(left, y - 5, w, 5);
            g.fillStyle = '#6b4426'; [left + 1, left + w - 3, x - 1].forEach(px => g.fillRect(px, top - 2, 2, wh));
            for (let i = 0; i < w + 4; i += 5) { g.fillStyle = pick(['#8e5cc9', '#f2c14e', '#2fb5b0'], i / 5); g.fillRect(left - 2 + i, top - rh, 5, rh); }
            return;
        }
        // walls
        const wallColor = kind === 'temple' || kind === 'school' || kind === 'tower' ? '#cfcac0' :
            kind === 'barn' ? '#a8432f' : kind === 'workshop' ? '#8a6040' : kind === 'dome' ? '#9aa3ad' : wall;
        g.fillStyle = wallColor; g.fillRect(left, wallTop, w, wh);
        g.fillStyle = shade(wallColor, -0.1);
        if (kind === 'temple' || kind === 'school' || kind === 'tower') {
            for (let yy = wallTop + 3; yy < y; yy += 4) for (let xx = left + ((yy / 4) % 2) * 3; xx < left + w; xx += 6) g.fillRect(xx, yy, 1, 4);
            for (let yy = wallTop + 3; yy < y; yy += 4) g.fillRect(left, yy, w, 1);
        } else {
            for (let yy = wallTop + 3; yy < y - 1; yy += 3) g.fillRect(left, yy, w, 1);
        }
        g.fillStyle = shade(wallColor, -0.3); g.fillRect(left, y - 2, w, 2);
        g.fillStyle = 'rgba(28,22,34,0.85)'; g.fillRect(left - 1, wallTop, 1, wh); g.fillRect(left + w, wallTop, 1, wh);
        // door
        const doorW = kind === 'barn' ? 10 : 6, doorH = kind === 'barn' ? 11 : 9;
        g.fillStyle = kind === 'barn' ? '#efe6d6' : '#5a3a22';
        g.fillRect(x - doorW / 2, y - doorH, doorW, doorH);
        if (kind === 'barn') {
            g.fillStyle = '#a8432f'; g.fillRect(x - doorW / 2 + 1, y - doorH + 1, doorW - 2, doorH - 1);
            g.fillStyle = '#efe6d6';
            for (let i = 0; i < doorH - 1; i++) { g.fillRect(x - doorW / 2 + 1 + i * (doorW - 2) / (doorH - 1), y - doorH + 1 + i, 1, 1); g.fillRect(x + doorW / 2 - 2 - i * (doorW - 2) / (doorH - 1), y - doorH + 1 + i, 1, 1); }
        } else { g.fillStyle = '#e2b04a'; g.fillRect(x + 1, y - 5, 1, 1); }
        // windows
        if (kind === 'house' || kind === 'school' || kind === 'workshop' || kind === 'shed') {
            windowAt(g, left + 4, wallTop + 4, lit);
            windowAt(g, left + w - 9, wallTop + 4, lit);
            if (lit) { lights.push([left + 6, wallTop + 6, 26]); lights.push([left + w - 7, wallTop + 6, 26]); }
        }
        if (kind === 'school') {
            g.fillStyle = '#efeae0'; [left + 1, left + w - 3].forEach(px => g.fillRect(px, wallTop, 2, wh));
        }
        if (kind === 'temple') {
            g.fillStyle = pick(['#c0392b', '#2d6cb5', '#d9a441', '#3d8a4a'], h); g.fillRect(x - 2, wallTop + 3, 4, 5);
            g.fillStyle = '#f2c14e'; g.fillRect(x - 1, wallTop + 2, 2, 1);
        }
        // roof
        if (kind === 'dome') {
            g.fillStyle = '#6f8fb0'; g.beginPath(); g.arc(x, wallTop, w / 2 - 2, Math.PI, 0); g.fill();
            g.fillStyle = '#a9c1d9'; g.beginPath(); g.arc(x - 4, wallTop - 6, 3, 0, Math.PI * 2); g.fill();
            g.fillStyle = '#3b3640'; g.fillRect(x, wallTop - w / 2 - 6, 1, 6);
        } else if (kind === 'tower') {
            g.fillStyle = '#b8b2a6';
            for (let i = 0; i < w; i += 4) g.fillRect(left + i, wallTop - 4, 3, 4);
        } else {
            roofBlock(g, left - 2, wallTop - rh, w + 4, rh, kind === 'barn' ? '#6b4a3a' : kind === 'temple' ? '#5a6070' :
                kind === 'workshop' ? '#5d5d66' : kind === 'school' ? '#3f5f8f' : roof);
        }
        if (kind === 'temple') {                    // steeple
            g.fillStyle = '#cfcac0'; g.fillRect(x - 4, wallTop - rh - 10, 8, 12);
            g.fillStyle = '#5a6070'; g.beginPath(); g.moveTo(x - 6, wallTop - rh - 10); g.lineTo(x, wallTop - rh - 20); g.lineTo(x + 6, wallTop - rh - 10); g.fill();
            g.fillStyle = '#f2c14e'; g.fillRect(x - 1, wallTop - rh - 24, 2, 4); g.fillRect(x - 2, wallTop - rh - 23, 4, 1);
            b._box = [left - 3, wallTop - rh - 26, w + 6, wh + rh + 28];
        }
        if (kind === 'house' || kind === 'workshop') {   // chimney and smoke when someone is in
            const cx = left + w - 8;
            g.fillStyle = '#7d5a4a'; g.fillRect(cx, wallTop - rh - 4, 4, 7);
            g.fillStyle = '#5c4034'; g.fillRect(cx - 1, wallTop - rh - 5, 6, 2);
            if (b.home_now > 0 || kind === 'workshop') {
                for (let i = 0; i < 3; i++) {
                    const t = ((now / 1600) + i / 3) % 1;
                    g.fillStyle = `rgba(220,220,225,${0.55 * (1 - t)})`;
                    g.beginPath(); g.arc(cx + 2 + Math.sin(t * 6 + i) * 2, wallTop - rh - 6 - t * 14, 1.5 + t * 2.5, 0, Math.PI * 2); g.fill();
                }
            }
        }
        if (kind === 'workshop') {                   // an anvil out front
            g.fillStyle = '#3b3b44'; g.fillRect(left + w + 2, y - 5, 6, 2); g.fillRect(left + w + 4, y - 3, 2, 3);
        }
    }

    function drawWell(g, w) {
        const x = Math.round(w.x * TILE + TILE / 2), y = Math.round(w.y * TILE + TILE / 2 + 4);
        g.fillStyle = 'rgba(0,0,0,0.22)'; g.beginPath(); g.ellipse(x, y + 1, 9, 3, 0, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#8f9098'; g.beginPath(); g.ellipse(x, y - 3, 8, 5, 0, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#2d4f6b'; g.beginPath(); g.ellipse(x, y - 4, 5, 3, 0, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#b5b6bd'; g.fillRect(x - 8, y - 4, 16, 1);
        g.fillStyle = '#6b4426'; g.fillRect(x - 7, y - 16, 2, 13); g.fillRect(x + 5, y - 16, 2, 13);
        g.fillStyle = '#8a5a3c'; g.beginPath(); g.moveTo(x - 10, y - 15); g.lineTo(x, y - 22); g.lineTo(x + 10, y - 15); g.fill();
        g.fillStyle = '#4a3322'; g.fillRect(x - 5, y - 13, 10, 1); g.fillRect(x, y - 13, 1, 5);
        g.fillStyle = '#7a6a55'; g.fillRect(x - 1, y - 9, 3, 3);
    }

    function drawLamp(g, l, lights) {
        const x = Math.round(l.x * TILE + TILE / 2), y = Math.round(l.y * TILE + TILE / 2 + 4);
        g.fillStyle = 'rgba(0,0,0,0.22)'; g.fillRect(x - 3, y, 7, 2);
        g.fillStyle = '#3b3640'; g.fillRect(x, y - 18, 2, 18); g.fillRect(x - 2, y - 1, 6, 2);
        g.fillStyle = '#2b2b2b'; g.fillRect(x - 2, y - 24, 6, 6);
        g.fillStyle = l.lit ? '#ffe27a' : (l.fuel > 0 ? '#c5ccd3' : '#7d858d');
        g.fillRect(x - 1, y - 23, 4, 4);
        g.fillStyle = '#2b2b2b'; g.fillRect(x - 3, y - 25, 8, 1);
        if (l.lit) lights.push([x + 1, y - 21, 7 * TILE, true]);
    }

    function drawGathering(g, ga, now, lights) {
        const x = Math.round(ga.x * TILE + TILE / 2), y = Math.round(ga.y * TILE + TILE / 2 + 4);
        if (!ga.on) {                                 // a signpost announcing it
            g.fillStyle = '#6b4426'; g.fillRect(x, y - 14, 2, 14);
            g.fillStyle = '#d9b77a'; g.fillRect(x - 6, y - 16, 14, 7);
            g.fillStyle = '#7a5230'; g.fillRect(x - 4, y - 14, 10, 1); g.fillRect(x - 4, y - 12, 8, 1);
            return;
        }
        // bunting round a bonfire
        const flags = ['#e05252', '#f2c14e', '#3f7fd9', '#46a35a', '#e07ab3'];
        g.fillStyle = '#6b4426'; g.fillRect(x - 26, y - 26, 2, 24); g.fillRect(x + 24, y - 26, 2, 24);
        g.strokeStyle = '#4a3322'; g.lineWidth = 0.6;
        g.beginPath(); g.moveTo(x - 25, y - 25); g.quadraticCurveTo(x, y - 17, x + 25, y - 25); g.stroke();
        for (let i = 0; i < 9; i++) {
            const t = (i + 0.5) / 9, fx = x - 25 + 50 * t, fy = y - 25 + 8 * 4 * t * (1 - t) * 0.95;
            g.fillStyle = flags[i % flags.length];
            g.beginPath(); g.moveTo(fx - 2, fy); g.lineTo(fx + 2, fy); g.lineTo(fx, fy + 4); g.fill();
        }
        g.fillStyle = '#7d7f87';
        for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; g.fillRect(x + Math.cos(a) * 6 - 1, y - 2 + Math.sin(a) * 3 - 1, 3, 2); }
        g.fillStyle = '#6b4426'; g.fillRect(x - 5, y - 3, 10, 2); g.fillRect(x - 1, y - 5, 2, 5);
        const f = Math.sin(now / 90) * 1.2;
        g.fillStyle = '#e8572a'; g.beginPath(); g.moveTo(x - 5, y - 2); g.quadraticCurveTo(x + f, y - 16, x + 5, y - 2); g.fill();
        g.fillStyle = '#f6b33d'; g.beginPath(); g.moveTo(x - 3, y - 2); g.quadraticCurveTo(x - f, y - 11, x + 3, y - 2); g.fill();
        g.fillStyle = '#fff1a8'; g.beginPath(); g.moveTo(x - 1.5, y - 2); g.quadraticCurveTo(x + f / 2, y - 7, x + 1.5, y - 2); g.fill();
        lights.push([x, y - 6, 6 * TILE, true]);
    }

    // ---------------------------------------------------------- characters
    function isNight(hour) { return hour >= 20 || hour < 6; }

    function agentState(a, now) {
        let s = T.agents.get(a.id);
        const to = { x: a.location.x, y: a.location.y };
        if (!s) {
            s = { id: a.id, from: to, to: to, t0: now, dur: 1, dir: 'down', look: lookFor(a), lastMove: 0 };
            T.agents.set(a.id, s);
        } else if (s.to.x !== to.x || s.to.y !== to.y) {
            const cur = posOf(s, now);
            const dist = Math.hypot(to.x - cur.x, to.y - cur.y);
            s.from = dist > 12 ? to : cur;
            s.to = to;
            s.t0 = now;
            s.dur = clamp(T.interval * 0.95, 120, 2500);
            const dx = to.x - cur.x, dy = to.y - cur.y;
            if (Math.abs(dx) + Math.abs(dy) > 0.02) {
                s.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
            }
        }
        if (s.stage !== a.life_stage) { s.stage = a.life_stage; s.look = lookFor(a); }
        s.data = a;
        return s;
    }

    function posOf(s, now) {
        const t = clamp((now - s.t0) / s.dur, 0, 1);
        return { x: s.from.x + (s.to.x - s.from.x) * t, y: s.from.y + (s.to.y - s.from.y) * t, moving: t < 1 && (s.from.x !== s.to.x || s.from.y !== s.to.y) };
    }

    function homeOf(a, buildingsById) {
        const b = a.home_id ? buildingsById.get(a.home_id) : null;
        if (!b || !b.complete || b.collapsed) return null;
        return Math.hypot(a.location.x - b.x, a.location.y - b.y) <= 3 ? b : null;
    }

    // --------------------------------------------------------------- camera
    function toScreen(wx, wy) {
        return [(wx - T.cam.x) * T.cam.zoom + T.W / 2, (wy - T.cam.y) * T.cam.zoom + T.H / 2];
    }
    function toWorld(sx, sy) {
        return [(sx - T.W / 2) / T.cam.zoom + T.cam.x, (sy - T.H / 2) / T.cam.zoom + T.cam.y];
    }
    function zoomLimits() {
        const mapW = (T.map ? T.map.width : 100) * TILE, mapH = (T.map ? T.map.height : 100) * TILE;
        return [Math.min(T.W / mapW, T.H / mapH), T.H / (7 * TILE)];
    }
    function defaultZoom() { return clamp(T.H / (24 * TILE), zoomLimits()[0], zoomLimits()[1]); }
    function setZoom(z, sx, sy) {
        const [lo, hi] = zoomLimits();
        const [wx, wy] = toWorld(sx, sy);
        T.cam.zoom = clamp(z, lo, hi);
        T.cam.x = wx - (sx - T.W / 2) / T.cam.zoom;
        T.cam.y = wy - (sy - T.H / 2) / T.cam.zoom;
    }

    function villageCentre(agents) {
        const alive = agents.filter(a => a.alive !== false);
        if (!alive.length) return null;
        const xs = alive.map(a => a.location.x).sort((a, b) => a - b);
        const ys = alive.map(a => a.location.y).sort((a, b) => a - b);
        const mid = Math.floor(alive.length / 2);
        return [xs[mid] * TILE + TILE / 2, ys[mid] * TILE + TILE / 2];
    }

    function updateCamera(now, data) {
        let target = null;
        if (T.mode === 'agent') {
            const s = T.agents.get(T.followId);
            if (s && s.data && s.data.alive !== false) {
                const p = posOf(s, now); target = [p.x * TILE + TILE / 2, p.y * TILE + TILE / 2];
            } else { T.mode = 'village'; T.followId = null; hideCard(); }
        }
        if (T.mode === 'village') target = villageCentre(data.agents || []);
        if (target) {
            const k = T.mode === 'agent' ? 0.12 : 0.04;
            T.cam.x += (target[0] - T.cam.x) * k;
            T.cam.y += (target[1] - T.cam.y) * k;
        }
        // keep the view on the map
        const mapW = (T.map ? T.map.width : 100) * TILE, mapH = (T.map ? T.map.height : 100) * TILE;
        const halfW = T.W / 2 / T.cam.zoom, halfH = T.H / 2 / T.cam.zoom;
        T.cam.x = halfW * 2 >= mapW ? mapW / 2 : clamp(T.cam.x, halfW, mapW - halfW);
        T.cam.y = halfH * 2 >= mapH ? mapH / 2 : clamp(T.cam.y, halfH, mapH - halfH);
    }

    // ---------------------------------------------------------------- input
    function minimapRect() {
        const size = Math.round(110 * T.dpr), pad = Math.round(10 * T.dpr);
        return [T.W - size - pad, T.H - size - pad, size, size];
    }

    function bindInput(canvas) {
        const pos = e => {
            const r = canvas.getBoundingClientRect();
            return [(e.clientX - r.left) * (T.W / r.width), (e.clientY - r.top) * (T.H / r.height)];
        };
        canvas.addEventListener('mousedown', e => {
            const [x, y] = pos(e);
            T.drag = { x, y, cx: T.cam.x, cy: T.cam.y };
            T.dragged = false;
        });
        window.addEventListener('mouseup', () => { T.drag = null; });
        canvas.addEventListener('mousemove', e => {
            const [x, y] = pos(e);
            T.mouse = { x, y, inside: true };
            if (T.drag) {
                const dx = x - T.drag.x, dy = y - T.drag.y;
                if (Math.abs(dx) + Math.abs(dy) > 4 * T.dpr) T.dragged = true;
                if (T.dragged) {
                    T.mode = 'free';
                    T.cam.x = T.drag.cx - dx / T.cam.zoom;
                    T.cam.y = T.drag.cy - dy / T.cam.zoom;
                }
            }
            canvas.style.cursor = T.drag && T.dragged ? 'grabbing' : (T.hover || T.hoverBuilding ? 'pointer' : 'grab');
        });
        canvas.addEventListener('mouseleave', () => { T.mouse.inside = false; T.hover = null; T.hoverBuilding = null; });
        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            const [x, y] = pos(e);
            if (T.mode === 'village') T.mode = 'free';
            setZoom(T.cam.zoom * Math.pow(1.0015, -e.deltaY), x, y);
        }, { passive: false });
        canvas.addEventListener('click', e => {
            if (T.dragged) { T.dragged = false; return; }
            const [x, y] = pos(e);
            const [mx, my, ms] = minimapRect();
            if (T.map && x >= mx && y >= my && x <= mx + ms && y <= my + ms) {
                T.mode = 'free';
                T.cam.x = (x - mx) / ms * T.map.width * TILE;
                T.cam.y = (y - my) / ms * T.map.height * TILE;
                return;
            }
            if (T.hover) { follow(T.hover.id); return; }
        });
    }

    function follow(id) {
        T.mode = 'agent';
        T.followId = id;
        if (T.cam.zoom < defaultZoom() * 1.3) setZoom(defaultZoom() * 1.5, T.W / 2, T.H / 2);
        showCard();
    }

    function buildControls(canvas) {
        const host = canvas.parentElement;
        if (!host) return;
        const bar = document.createElement('div');
        bar.className = 'town-controls';
        bar.style.cssText = 'position:absolute;top:10px;right:10px;display:flex;gap:6px;z-index:5;';
        const btn = (label, title, fn) => {
            const b = document.createElement('button');
            b.type = 'button'; b.textContent = label; b.title = title;
            b.style.cssText = 'background:rgba(15,23,42,0.88);color:#e2e8f0;border:1px solid #475569;border-radius:6px;' +
                'padding:4px 9px;font-size:13px;cursor:pointer;line-height:18px;';
            b.addEventListener('click', ev => { ev.stopPropagation(); fn(); });
            bar.appendChild(b);
            return b;
        };
        btn('＋', 'Zoom in', () => { if (T.mode === 'village') T.mode = 'free'; setZoom(T.cam.zoom * 1.3, T.W / 2, T.H / 2); });
        btn('－', 'Zoom out', () => { if (T.mode === 'village') T.mode = 'free'; setZoom(T.cam.zoom / 1.3, T.W / 2, T.H / 2); });
        btn('🎯 Village', 'Follow the village', () => { T.mode = 'village'; T.followId = null; hideCard(); setZoom(defaultZoom(), T.W / 2, T.H / 2); });
        btn('🗺️ Map', 'Show the whole map', () => {
            T.mode = 'free'; T.followId = null; hideCard();
            setZoom(zoomLimits()[0], T.W / 2, T.H / 2);
            if (T.map) { T.cam.x = T.map.width * TILE / 2; T.cam.y = T.map.height * TILE / 2; }
        });
        host.appendChild(bar);
        T.controls = bar;

        const card = document.createElement('div');
        card.className = 'town-card';
        card.style.cssText = 'position:absolute;right:10px;top:46px;width:230px;display:none;z-index:5;background:rgba(15,23,42,0.95);' +
            'border:1px solid #6366f1;border-radius:8px;padding:10px 12px;font-size:12px;color:#e2e8f0;line-height:1.5;';
        host.appendChild(card);
        T.card = card;
        card.addEventListener('click', ev => {
            const act = ev.target && ev.target.dataset ? ev.target.dataset.act : null;
            if (act === 'close') { T.mode = 'village'; T.followId = null; hideCard(); }
            if (act === 'profile' && T.followId && T.onProfile) T.onProfile(T.followId);
        });
    }

    function showCard() { if (T.card) { T.card.style.display = 'block'; T.cardKey = ''; } }
    function hideCard() { if (T.card) T.card.style.display = 'none'; }

    function updateCard(buildingsById) {
        if (!T.card || T.mode !== 'agent') return;
        const s = T.agents.get(T.followId);
        if (!s || !s.data) return;
        const a = s.data;
        const [emoji, phrase] = actionInfo(a.current_action);
        const home = a.home_id && buildingsById.get(a.home_id);
        const partner = a.partner_id && T.agents.get(a.partner_id);
        const job = a.job || a.occupation || '';
        const key = [a.name, a.current_action, a.dominant_emotion, home && home.name, partner && partner.data && partner.data.name,
            Math.round(a.health || 0), Math.round(a.energy || 0), job].join('|');
        if (key === T.cardKey) return;
        T.cardKey = key;
        T.card.innerHTML =
            `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">` +
            `<strong style="color:#a78bfa;font-size:14px;">${escapeHtml(a.name)}</strong>` +
            `<span data-act="close" style="cursor:pointer;color:#94a3b8;" title="Stop following">✕</span></div>` +
            `<div>${emoji} ${escapeHtml(phrase)}</div>` +
            `<div style="color:#94a3b8;">Age ${escapeHtml(a.age)} · ${escapeHtml(a.life_stage || '')}${job ? ' · ' + escapeHtml(job) : ''}</div>` +
            `<div style="color:#94a3b8;">Feeling ${escapeHtml(a.dominant_emotion || 'calm')} · health ${Math.round(a.health || 0)} · energy ${Math.round(a.energy || 0)}</div>` +
            `<div style="color:#94a3b8;">${home ? '🏠 ' + escapeHtml(home.name) : 'No home yet'}${partner && partner.data ? ' · 💞 ' + escapeHtml(partner.data.name) : ''}</div>` +
            `<button data-act="profile" type="button" style="margin-top:6px;background:#4f46e5;color:#fff;border:0;border-radius:5px;padding:3px 10px;cursor:pointer;">👤 Full profile</button>`;
    }

    // ------------------------------------------------------------- talking
    function noteConversations(data, now) {
        const events = data.recent_events || [];
        const byName = new Map((data.agents || []).map(a => [a.name, a.id]));
        events.forEach(e => {
            if (!e || !e.id || T.seenTalk.has(e.id) || !(e.title || '').startsWith('💬')) return;
            T.seenTalk.add(e.id);
            const lines = String(e.description || '').split(' / ');
            let at = now;
            lines.slice(0, 6).forEach(line => {
                const m = line.match(/^([^:]{1,40}):\s*(.+)$/);
                if (!m || !byName.has(m[1].trim())) return;
                const text = m[2].trim();
                const show = clamp(2500 + text.length * 45, 3000, 8000);
                T.speech.set(byName.get(m[1].trim()) + '|' + at, { id: byName.get(m[1].trim()), text, from: at, until: at + show });
                at += show;
            });
        });
        if (T.seenTalk.size > 300) T.seenTalk = new Set(Array.from(T.seenTalk).slice(-150));
        for (const [k, v] of T.speech) if (v.until < now) T.speech.delete(k);
    }

    function speakingNow(id, now) {
        for (const v of T.speech.values()) if (v.id === id && v.from <= now && now < v.until) return v.text;
        return null;
    }

    // ------------------------------------------------------------ overlays
    function roundRect(g, x, y, w, h, r) {
        g.beginPath();
        g.moveTo(x + r, y); g.lineTo(x + w - r, y); g.quadraticCurveTo(x + w, y, x + w, y + r);
        g.lineTo(x + w, y + h - r); g.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        g.lineTo(x + r, y + h); g.quadraticCurveTo(x, y + h, x, y + h - r);
        g.lineTo(x, y + r); g.quadraticCurveTo(x, y, x + r, y); g.closePath();
    }

    function wrap(g, text, maxW) {
        const words = text.split(/\s+/), lines = [];
        let line = '';
        words.forEach(w => {
            const t = line ? line + ' ' + w : w;
            if (g.measureText(t).width > maxW && line) { lines.push(line); line = w; } else line = t;
        });
        if (line) lines.push(line);
        if (lines.length > 3) { lines.length = 3; lines[2] = lines[2].replace(/.{0,2}$/, '…'); }
        return lines;
    }

    function bubble(g, sx, sy, content, isSpeech) {
        const d = T.dpr;
        g.font = isSpeech ? `${12 * d}px system-ui, sans-serif` : `${13 * d}px system-ui, sans-serif`;
        const lines = isSpeech ? wrap(g, content, 170 * d) : [content];
        const lh = (isSpeech ? 15 : 16) * d;
        const w = Math.max(...lines.map(l => g.measureText(l).width)) + 12 * d, h = lines.length * lh + 6 * d;
        const x = sx - w / 2, y = sy - h - 6 * d;
        g.fillStyle = 'rgba(255,255,255,0.95)'; g.strokeStyle = 'rgba(30,27,46,0.8)'; g.lineWidth = 1 * d;
        roundRect(g, x, y, w, h, 6 * d); g.fill(); g.stroke();
        g.beginPath(); g.moveTo(sx - 4 * d, y + h - 0.5); g.lineTo(sx, y + h + 5 * d); g.lineTo(sx + 4 * d, y + h - 0.5); g.closePath();
        g.fill(); g.beginPath(); g.moveTo(sx - 4 * d, y + h); g.lineTo(sx, y + h + 5 * d); g.lineTo(sx + 4 * d, y + h); g.stroke();
        g.fillStyle = '#1e1b2e'; g.textAlign = 'center'; g.textBaseline = 'middle';
        lines.forEach((l, i) => g.fillText(l, sx, y + 3 * d + lh * (i + 0.5)));
    }

    function label(g, text, sx, sy, color, size) {
        const d = T.dpr;
        g.font = `600 ${size * d}px system-ui, sans-serif`;
        g.textAlign = 'center'; g.textBaseline = 'top';
        g.lineWidth = 3 * d; g.strokeStyle = 'rgba(15,12,24,0.85)'; g.lineJoin = 'round';
        g.strokeText(text, sx, sy);
        g.fillStyle = color; g.fillText(text, sx, sy);
    }

    function tooltip(g, lines, sx, sy) {
        const d = T.dpr;
        g.font = `${12 * d}px system-ui, sans-serif`;
        const w = Math.max(...lines.map((l, i) => { g.font = i === 0 ? `bold ${13 * d}px system-ui, sans-serif` : `${12 * d}px system-ui, sans-serif`; return g.measureText(l).width; })) + 20 * d;
        const h = lines.length * 17 * d + 10 * d;
        let x = sx + 16 * d, y = sy - h / 2;
        if (x + w > T.W - 4) x = sx - w - 16 * d;
        y = clamp(y, 4, T.H - h - 4);
        g.fillStyle = 'rgba(15,23,42,0.96)'; g.strokeStyle = '#6366f1'; g.lineWidth = 2 * d;
        roundRect(g, x, y, w, h, 7 * d); g.fill(); g.stroke();
        g.textAlign = 'left'; g.textBaseline = 'top';
        lines.forEach((l, i) => {
            g.font = i === 0 ? `bold ${13 * d}px system-ui, sans-serif` : `${12 * d}px system-ui, sans-serif`;
            g.fillStyle = i === 0 ? '#c4b5fd' : i === lines.length - 1 ? '#818cf8' : '#e2e8f0';
            g.fillText(l, x + 10 * d, y + 6 * d + i * 17 * d);
        });
    }

    function darkness(h) {      // h: fractional hour
        if (h >= 7 && h < 18) return 0;
        if (h >= 18 && h < 20) return (h - 18) / 2 * 0.3;
        if (h >= 20 && h < 22) return 0.3 + (h - 20) / 2 * 0.28;
        if (h >= 22 || h < 5) return 0.58;
        if (h >= 5 && h < 7) return 0.58 * (1 - (h - 5) / 2);
        return 0;
    }

    // --------------------------------------------------------------- render
    function resize() {
        const c = T.canvas, host = c.parentElement;
        const cw = host ? host.clientWidth : c.clientWidth, ch = host ? host.clientHeight : c.clientHeight;
        if (!cw || !ch) return false;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = Math.round(cw * dpr), h = Math.round(ch * dpr);
        if (c.width !== w || c.height !== h) {
            const first = !T.W;
            c.width = w; c.height = h;
            T.W = w; T.H = h; T.dpr = dpr;
            if (first || T.mode === 'village') T.cam.zoom = defaultZoom();
            else setZoom(T.cam.zoom, w / 2, h / 2);
        }
        return true;
    }

    function render(ctx, data, worldExtras) {
        const t0 = performance.now();
        const now = Date.now();
        if (!T.canvas || !resize() || T.canvas.offsetParent === null) return;
        const g = ctx;
        const town = data.town || {};
        const hourF = (town.hour != null ? town.hour : (data.world && data.world.current_hour) || 12) + (town.minute || 0) / 60;
        const night = isNight(Math.floor(hourF));
        const dark = darkness(hourF);
        const buildings = town.buildings || [];
        const buildingsById = new Map(buildings.map(b => [b.id, b]));
        updateCamera(now, data);

        g.save();
        g.imageSmoothingEnabled = false;
        g.fillStyle = '#2a6fb0';
        g.fillRect(0, 0, T.W, T.H);
        g.setTransform(T.cam.zoom, 0, 0, T.cam.zoom, T.W / 2 - T.cam.x * T.cam.zoom, T.H / 2 - T.cam.y * T.cam.zoom);
        const [vx0, vy0] = toWorld(0, 0), [vx1, vy1] = toWorld(T.W, T.H);
        if (T.terrain) {
            const sx = clamp(Math.floor(vx0), 0, T.terrain.width), sy = clamp(Math.floor(vy0), 0, T.terrain.height);
            const sw = clamp(Math.ceil(vx1) - sx, 0, T.terrain.width - sx), sh = clamp(Math.ceil(vy1) - sy, 0, T.terrain.height - sy);
            if (sw > 0 && sh > 0) g.drawImage(T.terrain, sx, sy, sw, sh, sx, sy, sw, sh);
            // water shimmer on visible water
            const tx0 = Math.floor(vx0 / TILE), tx1 = Math.ceil(vx1 / TILE), ty0 = Math.floor(vy0 / TILE), ty1 = Math.ceil(vy1 / TILE);
            const phase = Math.floor(now / 500);
            g.fillStyle = 'rgba(200,235,255,0.55)';
            for (let ty = Math.max(0, ty0); ty < Math.min(T.map.height, ty1); ty++) {
                const row = T.map.terrain[ty];
                for (let tx = Math.max(0, tx0); tx < Math.min(T.map.width, tx1); tx++) {
                    if (row[tx] !== 'w' || (tx * 7 + ty * 13 + phase) % 9 !== 0) continue;
                    g.fillRect(tx * TILE + ((tx * 5 + phase) % 10), ty * TILE + ((ty * 3) % 12) + 2, 4, 1);
                }
            }
        }
        const works = data.infrastructure || {};
        buildRoads(works.roads || []);
        if (T.roads) g.drawImage(T.roads, 0, 0);

        // everything that stands up, drawn back to front
        const lights = [];
        const items = [];
        buildings.forEach(b => items.push([b.y * TILE + TILE / 2 + 6, 'b', b]));
        (works.wells || []).forEach(w => items.push([w.y * TILE + TILE / 2 + 4, 'w', w]));
        (works.lights || []).forEach(l => items.push([l.y * TILE + TILE / 2 + 4, 'l', l]));
        // a gathering shows from two hours before it starts until it ends
        const tickNow = town.tick || 0;
        const gatherings = (town.gatherings || []).filter(ga => ga.on || (tickNow < ga.start && ga.start - tickNow <= 12));
        gatherings.forEach(ga => items.push([ga.y * TILE + TILE / 2 + 4, 'g', ga]));
        const shown = [];
        (data.agents || []).forEach(a => {
            if (a.alive === false) return;
            const s = agentState(a, now);
            const p = posOf(s, now);
            const sleeping = night && a.current_action === 'rest';
            const indoors = sleeping && homeOf(a, buildingsById);
            if (indoors) { s.indoors = indoors; return; }
            s.indoors = null;
            s.screen = null;
            shown.push(s);
            items.push([p.y * TILE + TILE / 2 + 5, 'a', s, p, sleeping]);
        });
        // forget agents no longer in the snapshot
        if (T.agents.size > (data.agents || []).length) {
            const ids = new Set((data.agents || []).map(a => a.id));
            for (const id of T.agents.keys()) if (!ids.has(id)) T.agents.delete(id);
        }
        items.sort((a, b) => a[0] - b[0]);
        const margin = 3 * TILE;
        items.forEach(it => {
            const wy = it[0], wx = it[1] === 'a' ? it[3].x * TILE : it[2].x * TILE;
            if (wy < vy0 - margin || wy > vy1 + margin * 2 || wx < vx0 - margin * 2 || wx > vx1 + margin * 2) {
                if (it[1] === 'b') it[2]._box = null;
                return;
            }
            if (it[1] === 'b') drawBuilding(g, it[2], now, night, lights);
            else if (it[1] === 'w') drawWell(g, it[2]);
            else if (it[1] === 'l') drawLamp(g, it[2], lights);
            else if (it[1] === 'g') drawGathering(g, it[2], now, lights);
            else drawCharacter(g, it[2], it[3], it[4], now);
        });
        if (worldExtras) {
            try { worldExtras(g); } catch (err) { console.error('Town map extras:', err); }
        }
        g.setTransform(1, 0, 0, 1, 0, 0);

        // night: darkness with holes where there is light
        if (dark > 0) {
            if (!T.lightCanvas) T.lightCanvas = document.createElement('canvas');
            const L = T.lightCanvas;
            if (L.width !== T.W || L.height !== T.H) { L.width = T.W; L.height = T.H; }
            const lg = L.getContext('2d');
            lg.globalCompositeOperation = 'source-over';
            lg.clearRect(0, 0, T.W, T.H);
            lg.fillStyle = `rgba(10,16,44,${dark})`;
            lg.fillRect(0, 0, T.W, T.H);
            lg.globalCompositeOperation = 'destination-out';
            lights.forEach(([wx, wy, r]) => {
                const [sx, sy] = toScreen(wx, wy), sr = r * T.cam.zoom;
                if (sx < -sr || sy < -sr || sx > T.W + sr || sy > T.H + sr) return;
                const grad = lg.createRadialGradient(sx, sy, 0, sx, sy, sr);
                grad.addColorStop(0, 'rgba(0,0,0,0.9)'); grad.addColorStop(1, 'rgba(0,0,0,0)');
                lg.fillStyle = grad; lg.beginPath(); lg.arc(sx, sy, sr, 0, Math.PI * 2); lg.fill();
            });
            g.drawImage(L, 0, 0);
            g.globalCompositeOperation = 'lighter';
            lights.forEach(([wx, wy, r, warm]) => {
                if (!warm) return;
                const [sx, sy] = toScreen(wx, wy), sr = r * 0.6 * T.cam.zoom;
                const grad = g.createRadialGradient(sx, sy, 0, sx, sy, sr);
                grad.addColorStop(0, `rgba(255,190,90,${0.28 * dark / 0.58})`); grad.addColorStop(1, 'rgba(255,190,90,0)');
                g.fillStyle = grad; g.beginPath(); g.arc(sx, sy, sr, 0, Math.PI * 2); g.fill();
            });
            g.globalCompositeOperation = 'source-over';
        }
        if (hourF >= 17 && hourF < 19.5) {          // golden hour
            g.fillStyle = `rgba(255,150,70,${0.1 * Math.sin((hourF - 17) / 2.5 * Math.PI)})`;
            g.fillRect(0, 0, T.W, T.H);
        }
        drawWeather(g, town.weather, now);

        // labels, bubbles and hover, at screen size
        T.hover = null; T.hoverBuilding = null;
        const tilePx = TILE * T.cam.zoom;
        const showNames = tilePx >= 12 * T.dpr;
        const showBubbles = tilePx >= 15 * T.dpr;
        const scale = a => a.life_stage === 'baby' ? 0.55 : a.life_stage === 'child' ? 0.75 : 1;
        shown.forEach(s => {
            const p = posOf(s, now);
            const [sx, sy] = toScreen(p.x * TILE + TILE / 2, p.y * TILE + TILE / 2 + 5);
            const hgt = SPRITE_H * scale(s.data) * T.cam.zoom;
            s.screen = [sx, sy, hgt];
            if (T.mouse.inside && Math.abs(T.mouse.x - sx) < Math.max(8 * T.dpr, 7 * T.cam.zoom) &&
                T.mouse.y < sy + 3 * T.dpr && T.mouse.y > sy - Math.max(hgt, 14 * T.dpr)) T.hover = s.data;
        });
        shown.forEach(s => {
            const [sx, sy, hgt] = s.screen;
            const a = s.data;
            const focus = (T.hover && T.hover.id === a.id) || T.followId === a.id;
            if (showNames || focus) label(g, a.name, sx, sy + 2 * T.dpr, focus ? '#fde68a' : '#ffffff', 11);
            const said = speakingNow(a.id, now);
            const sleeping = night && a.current_action === 'rest';
            if (said) bubble(g, sx, sy - hgt, said, true);
            else if (showBubbles || focus) bubble(g, sx, sy - hgt, sleeping ? '💤' : actionInfo(a.current_action)[0], false);
        });
        // homes with someone asleep inside
        const sleepers = new Map();
        for (const s of T.agents.values()) if (s.indoors) sleepers.set(s.indoors.id, (sleepers.get(s.indoors.id) || 0) + 1);
        buildings.forEach(b => {
            if (!b._box) return;
            const [bx, by, bw, bh] = b._box;
            const [sx, sy] = toScreen(bx, by), [ex, ey] = toScreen(bx + bw, by + bh);
            if (sleepers.has(b.id) && showBubbles) {
                label(g, '💤' + (sleepers.get(b.id) > 1 ? ' ×' + sleepers.get(b.id) : ''), (sx + ex) / 2, sy - 16 * T.dpr, '#c7d2fe', 11);
            }
            if (!T.hover && T.mouse.inside && T.mouse.x >= sx && T.mouse.x <= ex && T.mouse.y >= sy && T.mouse.y <= ey) T.hoverBuilding = b;
        });
        gatherings.forEach(ga => {
            if (!showBubbles) return;
            const [sx, sy] = toScreen(ga.x * TILE + TILE / 2, ga.y * TILE + TILE / 2 - 30);
            const when = ga.on ? `🎉 ${ga.host}'s ${ga.kind}` : `📣 ${ga.kind} at ${String(Math.floor(ga.start / 6) % 24).padStart(2, '0')}:00`;
            label(g, when, sx, sy, '#fde68a', 11);
        });

        drawMinimap(g, data, buildings);
        drawClock(g, data, hourF);

        if (T.hover && !(T.drag && T.dragged)) {
            const a = T.hover, [emoji, phrase] = actionInfo(a.current_action);
            const home = a.home_id && buildingsById.get(a.home_id);
            tooltip(g, [a.name, `${emoji} ${phrase}`, `Age ${a.age} · ${a.life_stage || ''} · feeling ${a.dominant_emotion || 'calm'}`,
                home ? `🏠 ${home.name}` : 'No home yet', 'Click to follow'], T.mouse.x, T.mouse.y);
        } else if (T.hoverBuilding && !(T.drag && T.dragged)) {
            const b = T.hoverBuilding;
            const status = b.collapsed ? 'Collapsed' : b.complete ? `${buildingKind(b)} · ${Math.round(b.durability * 100)}% sound` : `Being built · ${Math.round(b.progress * 100)}%`;
            const people = b.residents && b.residents.length ? `Home of ${b.residents.slice(0, 4).join(', ')}${b.residents.length > 4 ? '…' : ''}` : (b.purposes || []).join(', ') || b.category;
            tooltip(g, [b.name, status, people].concat(b.home_now ? [`${b.home_now} at home now`] : []), T.mouse.x, T.mouse.y);
        }
        g.restore();
        updateCard(buildingsById);
        T.frameMs = T.frameMs * 0.95 + (performance.now() - t0) * 0.05;
    }

    function drawCharacter(g, s, p, sleeping, now) {
        const a = s.data;
        const sc = a.life_stage === 'baby' ? 0.55 : a.life_stage === 'child' ? 0.75 : 1;
        const x = p.x * TILE + TILE / 2, y = p.y * TILE + TILE / 2 + 5;
        if (sleeping) {                                  // asleep outdoors, on a bedroll
            const look = s.look;
            g.fillStyle = 'rgba(0,0,0,0.22)'; g.fillRect(x - 9, y - 1, 18, 3);
            g.fillStyle = shade(look.shirt, -0.2); g.fillRect(x - 8, y - 6, 15, 6);
            g.fillStyle = shade(look.shirt, 0.15); g.fillRect(x - 8, y - 6, 15, 1);
            g.fillStyle = '#efece2'; g.fillRect(x + 4, y - 7, 6, 6);
            g.fillStyle = look.skin; g.fillRect(x + 5, y - 7, 4, 4);
            g.fillStyle = look.hair; g.fillRect(x + 7, y - 8, 3, 5);
            return;
        }
        let frame = 0;
        if (p.moving) frame = [1, 0, 2, 0][Math.floor(now / 140) % 4];
        let dir = s.dir;
        if (!p.moving && (a.current_action === 'socialize' || a.current_action === 'tell_story' || a.current_action === 'teach')) {
            let best = null, bd = 3;
            for (const o of T.agents.values()) {
                if (o === s || !o.to) continue;
                const d = Math.hypot(o.to.x - s.to.x, o.to.y - s.to.y);
                if (d < bd) { bd = d; best = o; }
            }
            if (best) {
                const dx = best.to.x - s.to.x, dy = best.to.y - s.to.y;
                dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
            }
        }
        const img = sprite(s.look, dir, frame);
        const w = SPRITE_W * sc, h = SPRITE_H * sc;
        const bob = !p.moving && Math.floor((now + hash(a.id) % 1000) / 700) % 2 ? 0.5 : 0;
        g.fillStyle = 'rgba(0,0,0,0.25)';
        g.beginPath(); g.ellipse(x, y, 5 * sc, 2 * sc, 0, 0, Math.PI * 2); g.fill();
        g.drawImage(img, Math.round(x - w / 2), Math.round(y - h + 1 + bob), w, h);
        if (T.followId === a.id) {
            g.strokeStyle = 'rgba(253,230,138,0.9)'; g.lineWidth = 1;
            g.beginPath(); g.ellipse(x, y, 8 * sc, 3.5 * sc, 0, 0, Math.PI * 2); g.stroke();
        }
    }

    function drawWeather(g, weather, now) {
        if (!weather) return;
        const d = T.dpr;
        if (weather === 'rainy' || weather === 'stormy') {
            const n = weather === 'stormy' ? 160 : 90;
            while (T.rain.length < n) T.rain.push([Math.random() * T.W, Math.random() * T.H, 0.6 + Math.random() * 0.6]);
            T.rain.length = n;
            g.strokeStyle = 'rgba(190,210,240,0.45)'; g.lineWidth = 1 * d;
            g.beginPath();
            T.rain.forEach(r => {
                r[1] += 14 * d * r[2]; r[0] -= 3 * d * r[2];
                if (r[1] > T.H) { r[1] = -10; r[0] = Math.random() * T.W * 1.2; }
                g.moveTo(r[0], r[1]); g.lineTo(r[0] - 3 * d, r[1] + 11 * d * r[2]);
            });
            g.stroke();
            g.fillStyle = 'rgba(40,55,80,0.12)'; g.fillRect(0, 0, T.W, T.H);
            if (weather === 'stormy' && (now % 7000) < 90) { g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(0, 0, T.W, T.H); }
        } else if (weather === 'snowy' || weather === 'blizzard') {
            const n = weather === 'blizzard' ? 220 : 110;
            while (T.rain.length < n) T.rain.push([Math.random() * T.W, Math.random() * T.H, 0.5 + Math.random()]);
            T.rain.length = n;
            g.fillStyle = 'rgba(255,255,255,0.85)';
            T.rain.forEach(r => {
                r[1] += 1.2 * d * r[2]; r[0] += Math.sin((now / 900) + r[2] * 9) * 0.6 * d + (weather === 'blizzard' ? 2.5 * d : 0);
                if (r[1] > T.H) { r[1] = -4; r[0] = Math.random() * T.W; }
                if (r[0] > T.W) r[0] = 0;
                g.fillRect(r[0], r[1], 2 * d * r[2], 2 * d * r[2]);
            });
            g.fillStyle = 'rgba(230,240,255,0.10)'; g.fillRect(0, 0, T.W, T.H);
        } else {
            T.rain.length = 0;
            if (weather === 'foggy') { g.fillStyle = 'rgba(220,225,235,0.28)'; g.fillRect(0, 0, T.W, T.H); }
            if (weather === 'heat_wave' || weather === 'drought') { g.fillStyle = 'rgba(255,170,60,0.08)'; g.fillRect(0, 0, T.W, T.H); }
            if (weather === 'cloudy') { g.fillStyle = 'rgba(60,70,90,0.08)'; g.fillRect(0, 0, T.W, T.H); }
        }
    }

    function drawMinimap(g, data, buildings) {
        if (!T.mini || !T.map) return;
        const [x, y, s] = minimapRect();
        const d = T.dpr;
        g.fillStyle = 'rgba(15,23,42,0.85)'; g.fillRect(x - 3 * d, y - 3 * d, s + 6 * d, s + 6 * d);
        g.imageSmoothingEnabled = false;
        g.drawImage(T.mini, x, y, s, s);
        const k = s / T.map.width;
        g.fillStyle = '#b9ad92';
        ((data.infrastructure || {}).roads || []).forEach(([rx, ry]) => g.fillRect(x + rx * k, y + ry * k, Math.max(1, k), Math.max(1, k)));
        buildings.forEach(b => {
            if (b.collapsed) return;
            g.fillStyle = b.complete ? '#b5473a' : '#e0a33a';
            g.fillRect(x + b.x * k - 1.5 * d, y + b.y * k - 1.5 * d, 3 * d, 3 * d);
        });
        g.fillStyle = '#ffffff';
        (data.agents || []).forEach(a => { if (a.alive !== false) g.fillRect(x + a.location.x * k - d, y + a.location.y * k - d, 2 * d, 2 * d); });
        const [vx0, vy0] = toWorld(0, 0), [vx1, vy1] = toWorld(T.W, T.H);
        g.strokeStyle = '#fde68a'; g.lineWidth = 1.5 * d;
        g.strokeRect(x + clamp(vx0 / TILE, 0, 100) * k, y + clamp(vy0 / TILE, 0, 100) * k,
            (clamp(vx1 / TILE, 0, T.map.width) - clamp(vx0 / TILE, 0, T.map.width)) * k,
            (clamp(vy1 / TILE, 0, T.map.height) - clamp(vy0 / TILE, 0, T.map.height)) * k);
    }

    function drawClock(g, data, hourF) {
        const d = T.dpr;
        const day = (data.world && data.world.current_day) || 1;
        const h = Math.floor(hourF), m = Math.round((hourF - h) * 60);
        const icon = h >= 6 && h < 18 ? '☀️' : h >= 18 && h < 20 ? '🌇' : '🌙';
        const text = `${icon} Day ${day} · ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
        g.font = `600 ${12 * d}px system-ui, sans-serif`;
        const w = g.measureText(text).width + 18 * d;
        const [mx, my] = minimapRect();
        const x = mx + 110 * d - w, y = my - 30 * d;
        g.fillStyle = 'rgba(15,23,42,0.88)'; roundRect(g, x, y, w, 22 * d, 11 * d); g.fill();
        g.fillStyle = '#e2e8f0'; g.textAlign = 'left'; g.textBaseline = 'middle';
        g.fillText(text, x + 9 * d, y + 11 * d);
    }

    // ---------------------------------------------------------------- API
    function update(data) {
        if (!data || !data.agents) return;
        const now = Date.now();
        if (T.lastUpdate) T.interval = T.interval * 0.7 + clamp(now - T.lastUpdate, 50, 5000) * 0.3;
        T.lastUpdate = now;
        T.data = data;
        const tick = data.town ? data.town.tick : (data.world && data.world.total_ticks) || 0;
        if (!T.map || tick < T.mapTick) loadMap(tick);
        (data.agents || []).forEach(a => { if (a.alive !== false) agentState(a, now); });
        noteConversations(data, now);
    }

    function init(canvas, opts) {
        T.canvas = canvas;
        T.onProfile = opts && opts.onProfile;
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.cursor = 'grab';
        bindInput(canvas);
        buildControls(canvas);
        resize();
        loadMap(0);
    }

    window.TownMap = {
        init, update, render,
        worldPx: loc => ({ x: loc.x * TILE + TILE / 2, y: loc.y * TILE + TILE / 2 }),
        tile: TILE,
        hoveredAgent: () => T.hover,
        // where each visible character's feet are, in CSS pixels within the canvas
        visibleAgents: () => {
            const out = [];
            for (const s of T.agents.values()) {
                if (!s.screen || !s.data) continue;
                out.push({ id: s.id, name: s.data.name, x: s.screen[0] / T.dpr, y: s.screen[1] / T.dpr });
            }
            return out;
        },
        follow,
        stats: () => ({ frameMs: T.frameMs, agents: T.agents.size, zoom: T.cam.zoom, mode: T.mode, mapLoaded: !!T.map, W: T.W, H: T.H }),
    };
})();
