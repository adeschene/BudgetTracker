import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "budget_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT,
                amount INTEGER NOT NULL,
                category_id INTEGER,
                account_id INTEGER,
                transaction_type TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                keywords TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                last_updated TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS net_worth_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                asset_type TEXT,
                value INTEGER NOT NULL,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT UNIQUE NOT NULL,
                asset_type TEXT,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER UNIQUE NOT NULL,
                monthly_target INTEGER NOT NULL,
                notes TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE NOT NULL,
                account_id INTEGER NOT NULL,
                date_column TEXT NOT NULL,
                description_column TEXT NOT NULL,
                description2_column TEXT,
                description_delimiter TEXT DEFAULT ' - ',
                amount_column TEXT,
                debit_column TEXT,
                credit_column TEXT,
                skip_rows INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS description_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                rule_order INTEGER NOT NULL,
                pattern TEXT NOT NULL,
                replacement TEXT NOT NULL,
                category_id INTEGER,
                ignore INTEGER DEFAULT 0,
                FOREIGN KEY (template_id) REFERENCES import_templates(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        ''')

        # Ensure default categories exist and run lightweight migrations if no custom cats exist
        if not self.get_categories():
            self._insert_default_categories(cursor)

        conn.commit()
        conn.close()
    
    def _insert_default_categories(self, cursor):
        default_categories = [
            ('Groceries', 'expense', 'grocery,groceries,supermarket,supermarkets,market,food market,foodmart,food lion,food city,food bazaar,food 4 less,food-4-less,foodland,food town,foodtown,foodco,corner market,corner store,mini mart,minimart,fresh market,fresh grocer,fresh thyme,farmers market,produce market,fruit market,veg market,whole foods,wholefoods,wholefds,whole fds,wholefd,whole fd,wholef,diet food,health food,natural grocers,organic market,organic grocer,aldi,aldi us,aldi inc,lidl,kroger,kroger co,fry\'s food,ralphs,king soopers,smiths food,fred meyer,safeway,vons,pavilions,albertsons,jewel osco,acme markets,shaws,star market,randalls,tom thumb,haggen,heb,h-e-b,meijer,giant,giant food,giant eagle,stop & shop,stater bros,stater brothers,hannaford,winco,winco foods,smart & final,smart and final,price chopper,harris teeter,shoprite,shop rite,wegmans,public,publix,save mart,save-mart,save a lot,save-a-lot,supervalu,super value,pick n save,pick-n-save,picknsave,hy-vee,hyvee,bashas,frys marketplace,city market,grocery outlet,groceryoutlet,market basket,marketbasket,wholefoods market,trader joes,trader joe\'s,trader joe,trder joes,aldi grocery,instacart,doordash grocery,ubereats grocery,amazon fresh,amazonfresh,amzn fresh,amznfresh,amazon pantry,amazonpantry,walmart grocery,walmart supercenter,walmart neighborhood market,target grocery,target super,target superstore,target supercenter,costco wholesale,costco whse,costco whsl,sams club,sam\'s club,bjs wholesale,bj\'s wholesale,bj\'s,bjs,metro market,metro grocery,asian market,latin market,indian market,halal market,kosher market,99 ranch,hmart,h mart,seafood city,el super,supermercado,super mercado,la michoacana,cardenas market,northgate market,rancho markets,sprouts farmers,sprouts,sprouts fm,sprouts mkt,earth fare,farm fresh,farmfresh,food depot,piggly wiggly,pigglywiggly,ingles markets,ingles,festival foods,festival food,kings food,foodarama,foodfair,food fair,food giant,food basics,grocer,grocers,coop market,food co-op,food coop,corner grocery,local grocery,neighborhood market,community market,discount grocery,dollar fresh,dollar general market,dg market,family dollar grocery,pantry,pantries,food warehouse,warehouse foods,warehouse grocery,ethnic market,bulk foods,bulk food,produce,meat market,butcher shop,bodega,tienda,mercado'),
            ('Dining', 'expense', 'restaurant,restaurants,diner,diners,eatery,eateries,bistro,bistros,cafe,cafes,café,cafés,coffee shop,coffeehouse,coffee house,bar,pub,tavern,brasserie,steakhouse,steak house,seafood restaurant,italian restaurant,italian,chinese restaurant,chinese,japanese restaurant,japanese,thai restaurant,thai,mexican restaurant,mexican,indian restaurant,indian,pizza,pizzeria,pizzahut,pizza hut,dominos,domino\'s,papajohns,papa johns,subway,quiznos,quizno\'s,mcdonalds,mcdonald\'s,mcd,burger king,bk,wendy\'s,wendys,taco bell,arbys,arbys roast beef,checkers,rallys,rally\'s,sonic drive-in,sonic,carls jr,carl\'s jr,hardees,hardee\'s,jack in the box,jackinthebox,in-n-out,in-n-out burger,chipotle,moes,moes southwest,qdoba,fuddruckers,applebees,applebee\'s,dennys,denny\'s,ihop,bob evans,crackers barrel,cracker barrel,chilis,chili\'s,texas roadhouse,outback steakhouse,outback,longhorn steakhouse,rainforest cafe,hardrock cafe,hard rock cafe,bubba gump,planet hollywood,cheesecake factory,cheescake factory,pf changs,pfchangs,p.f.changs,macaroni grill,tgi fridays,tgifridays,friday\'s,red lobster,redlobster,bonefish grill,carrabbas,carrabba\'s,maggianos,maggiano\'s,olive garden,olivgarden,bennigans,bennigan\'s,tony romas,tony roma\'s,ruby tuesday,rubytuesday,perkins,perkins restaurant,bakers square,ground round,friendlys,friendly\'s,howard johnsons,hojos,hojo\'s,shoneys,shoney\'s,waffle house,wafflehouse,international house of pancakes,dunkin donuts,dunkin\',dunkindonuts,starbucks,starbucks coffee,dunn bros,dunn bros coffee,tim hortons,timhortons,tim\'s,peets coffee,peets,caribou coffee,caribou,dutch bros,dutchbros,cozymeal,blue apron,hello fresh,hellofresh,meal kit,delivery,takeout,ubereats,doordash,grubhub,postmates,doordash delivery,ubereats delivery,grubhub delivery,eatstreet,seamless,delivery.com,food delivery,restaurant delivery,to go,carry out,take away,drive thru,drive-thru,drive through,buffet,all you can eat,brown bag,del taco,del-taco,white castle,whitecastle,kfc,kentucky fried chicken,kfc chicken,popeyes,popeye\'s,churchs chicken,church\'s chicken,bo jangles,bojangels,raising canes,raising cane\'s,chikfila,chick-fil-a,zaxbys,zaxby\'s,popeyes chicken,wingstop,wings,bbq,barbecue,bar-b-que,smokehouse,smokey bones,smokeybones,rub,texas bbq,ribs,draft house,drafthouse,brew pub,brewpub,craft beer,local brewery,tap house,taproom,gastropub,food truck,street food,fusion restaurant,farm to table,organic eatery,sushi bar,sushi,sashimi,ramen shop,ramen,pho shop,pho,vietnamese restaurant,korean bbq,kbbq,bbq joint,hot pot,dim sum,brunch spot,brunch cafe,dessert bar,ice cream shop,gelato,crepe stand,juice bar,smoothie king,smoothie,jamba juice,jamba,naked juice,robeks,juices for life,barnes & noble cafe,barnes cafe,airport cafe,hotel restaurant,room service,casino dining,venue food,concession stand,ballpark food,stadium eats'),
            ('Transportation', 'expense', 'taxi,taxis,cab,cabs,uber,lyft,lyft ride,didi,bolt,via,ola,carmel,arro,yandex go,airport taxi,black car,limo,limousine,livery,shuttle,airport shuttle,hotel shuttle,super shuttle,super-shuttle,transit,public transit,bus,buses,septa,mta,nycta,mbta,cta,chicago transit,la metro,lacmta,dc metro,wmata,bart,sfmta,caltrain,ace train,amtrak,amtrak train,train,rail,railroad,metro,metra,metrolink,light rail,streetcar,tram,trams,underground,tube,lrt,go train,via rail,brightline,acela,bullet train,high speed rail,ferry,ferries,staten island ferry,water taxi,boat,boating,charter boat,airplane,flight,airline,delta,united,american airlines,aa,ua,dl,southwest,jetblue,frontier,spirit,alaska airlines,airline ticket,airport,plane ticket,airfare,gas station,gas,gasoline,exxon,mobil,shell,chevron,bp,76 gas,arco,76,conoco,phillips 66,sinclair,marathon gas,sunoco,hess,waWa gas,quick mart gas,fuel,filling station,service station,car wash,carwash,detail shop,auto repair,auto service,jiffy lube,Meineke,firestone,monro muffler,pep boys,ntb,autozone,oreilly auto,advance auto parts,schucks,carquest,aaa roadside,towing,tow truck,aaa,tolls,toll road,ezpass,fastag,sunpass,ipass,ez-pass,toll plaza,bridge toll,tunnel toll,parking,parking garage,parking lot,pay station,spot hero,parking.com,airport parking,parkwhiz,parkmobile,zipcar,carshare,turo,getaround,enterprise carshare,hertz 24/7,car rental,avis,budget,hertz,enterprise,alamo,national car rental,thrifty,dollar rent a car,sixt,six rent a car,airport rental,bike share,citi bike,divvy,blue bike,spin,lyft bike,bird,lime scooter,jump bike,scooter rental,e-scooter,e-bike,transpo,transit app,transit pass,membership transit,commuter pass,monthly pass'),
            ('Utilities', 'expense', 'electric,electricity,pge,pacific gas,pg&e,edison,sce,southern california edison,duke energy,com ed,commonwealth edison,aep,american electric,aps,aztec electric,nve energy,nv energy,centerpoint energy,gas company,socalgas,southern california gas,pg&e gas,national grid,con edison,consolidated edison,water,water company,ladwp,los angeles water,dc water,seattle public utilities,seattle water,san diego water,sdcwa,ebmud,east bay water,smwd,santa monica water,dwp,department of water,puc,public utilities commission,sewer,sanitation,sewerage,wastewater,trash,garbage,waste management,wm,republic services,waste connections,sanitation services,internet,comcast,xfinity,spectrum,charter,at&t internet,uverse,verizon fios,fios,frontier communications,century link,centurylink,cox internet,cox cable,bright house,brighthouse,windstream,consolidated communications,cable,cablevision,optimum online,rcn,mediacom,suddenlink,phone,telephone,at&t phone,verizon phone,frontier phone,comcast phone,sbc phone,pacbell,pacific bell,phone bill,telecom,telecommunications,satellite tv,directv,dish network,dish,direct tv,sky tv,comcast cable,xfinity tv,spectrum tv,fios tv,cable tv,pay tv,utility bill,pscu,municipal utilities,city utilities,coop electric,rural electric,telephone coop'),
            ('Entertainment', 'expense', 'movie,movies,cinema,theater,theatre,amc,regal,cinemark,amc Theatres,regal cinemas,imdb,netflix,hulu,disney+,hbomax,paramount+,peacock,amazon prime video,prime video,spotify,apple music,youtube premium,concert,concerts,ticketmaster,live nation,stubhub,seatgeek,axs,tickets,venue,bandsintown,spotify live,concert tickets,music festival,coachella,lollapalooza,bonnaroo,edm festival,ultra music,rave,club,night club,nightclub,dance club,strip club,gentlemans club,pole dancing,arcade,amusement park,disneyland,disney world,universal studios,six flags,disney land,universal orlando,busch gardens,knott\'s berry farm,legoland,water park,splash zone,theme park,zoo,aquarium,seaworld,museum,art museum,science museum,natural history museum,smithsonian,met museum,louvre,planetarium,opera,ballet,symphony,orchestra,broadway,play,billboard,off broadway,musical theater,comedy club,stand up,improv,roast battle,improv comedy,improvise,standup comedy,netflix comedy,books bookstore,barnes and noble,barnes&noble,books-a-million,bn.com,amazon books,bookshop,library,game stop,gamestop,ebgames,comic book,comiccon,comic con,sdcc,nycc,anime expo,otakon,comic shop,card shop,magic the gathering,mtg,pokemon cards,trading cards,sports,nfl,nba,ncaa,mlb,nhl,mma,ufc,boxing,wwe,wrestling,f1,racing,nascar,formula 1,indycar,super bowl,world series,final four,march madness,olympics,superbowl,worldcup,soccer,football,basketball,baseball,hockey,golf,pga masters,masters golf,us open,gambling,casino,mgm,mirage,caesars,pokerstars,betmgm,draftkings,fanduel,bet365,sportsbook,vegas,ballys,circus circus,slot machine,blackjack,roulette,bowling,bowling alley,topgolf,axethrowing,darts,pool hall,billiards,karaoke,kj night,karaoke bar,escape room,virtual reality,vr arcade,augmented reality,go kart,karting,raceway,mini golf,putt putt,go-kart,batting cage,trampoline park,sky zone,indoor skydiving,ifly,rock climbing,gymkhana,adventure park,ropes course,zipline,laser tag,paintball,airsoft,go ape,high ropes,video rental,redbox,blockbuster,dvd,bluray,comcast tv,roku,fire tv,apple tv,chromecast,smart tv,streaming device'),
            ('Shopping', 'expense', 'amazon,amazon.com,ebay,ebay.com,walmart,walmart.com,target,target.com,best buy,bestbuy.com,macys,macys.com,kohls,kohls.com,home depot,homedepot.com,lowes,lowes.com,ikea,ikea.com,costco,costco.com,samsclub.com,bjs.com,wholefoods.com,traderjoes.com,staples,staples.com,office depot,officedepot.com,office max,officemax.com,michaels,michaels.com,joann,joann.com,hobby lobby,hobbylobby.com,bed bath,beyond,bedbathandbeyond.com,pottery barn,potterybarn.com,williams sonoma,williamssonoma.com,crate barrel,crateandbarrel.com,west elm,westelm.com,cb2,cb2.com,wayfair,wayfair.com,overstock,overstock.com,etsy,etsy.com,zappos,zappos.com,nike,nike.com,adidas,adidas.com,under armour,underarmour.com,dick\'s sporting goods,dickssportinggoods.com,rei,rei.com,academy sports,academysports.com,bass pro,basspro.com,cabelas,cabelas.com,ulta,ulta.com,sephora,sephora.com,mac cosmetics,maccosmetics.com,ulta beauty,sally beauty,sallybeauty.com,avon,avon.com,mary kay,marykay.com,party lite,partylite.com,target optical,pearle vision,lenscrafters,lenscrafters.com,warby parker,warbyparker.com,old navy,oldnavy.com,gap,gap.com,banana republic,bananarepublic.com,athleta,athleta.com,madewell,madewell.com,j crew,jcrew.com,jcrew factory,abercrombie,fitch,hollister,hollisterco.com,american eagle,ae.com,aerie,aerie.com,forever 21,forever21.com,hm,hm.com,zara,zara.com,asos,asos.com,shein,shein.com,boohoo,boohoo.com,pretty little thing,prettylittlething.com,nordstrom,nordstrom.com,nordstrom rack,nordstromrack.com,saks fifth avenue,saksfifthavenue.com,bloomingdales,bloomingdales.com,neiman marcus,neimanmarcus.com,belk,belk.com,dillards,dillards.com,jcpenney,jcpenney.com,sears,sears.com,kmart,kmart.com,ross,rossstores.com,tj maxx,tjmaxx.com,marshalls,marshalls.com,burlington,burlington.com,goodwill,salvation army,savers,thrift store,consignment,petco,petco.com,petsmart,petsmart.com,chewy,chewy.com,ace hardware,acehardware.com,true value,truevalue.com,harbor freight,harborfreight.com,tractor supply,tractorsupply.com,menards,menards.com,build a bear,buildabear.com,toys r us,toysrus.com,gamestop.com,hot topic,hottopic.com,spencers,spencersonline.com,american girl,americangirl.com,disney store,disneystore.com,lego,legostore.com,hallmark,hallmark.com,joann fabrics,apple store,apple.com,microsoft store,microsoftstore.com,samsung experience,samsung.com,home goods,homegoods.com,pier 1,pier1.com,container store,containerstore.com,world market,worldmarket.com,cost plus,costplus.com,tjmaxx,homegoods,shopping mall,mall,retail,outlet mall,premium outlet,simon malls,westfield mall,wait no shopping,visa,mastercard,amex no shopping,buy now pay later,affirm,afterpay,klarna,zip pay'),
            ('Healthcare', 'expense', 'doctor,doctors,physician,physicians,clinic,clinics,medical center,medical group,urgent care,walk in clinic,walk-in clinic,er,emergency room,hospital,hospitals,healthcare,health care,kaiser,kaiser permanente,permanente medical,sutter health,sutter,sanitas medical,one medical,onemedical,concentra,concentra medical,minute clinic,cvs minuteclinic,walgreens clinic,health hub,primary care,family practice,pediatrician,pediatrics,dentist,dentists,dental,dental care,orthodontist,periodontist,dental clinic,dds,dmd,oral surgeon,eye doctor,optometrist,ophthalmologist,eye care,vision care,lasik,contact lens,glasses,eyeglasses,walman optical,vet,veterinarian,veterinary,vet clinic,animal hospital,pharmacy,pharmacies,cvs,cvs pharmacy,walgreens,rite aid,walgreens pharmacy,riteaid,wal mart pharmacy,target pharmacy,kroger pharmacy,publix pharmacy,giant eagle pharmacy,longs drugs,longs,savon drugs,osco pharmacy,walmart pharmacy,costco pharmacy,sams pharmacy,good neighbor pharmacy,duane reade,duane reade pharmacy,brooklyn pharmacy,apotheke,health mart,independent pharmacy,rx,prescription,lab,labcorp,quest diagnostics,quest labs,lab draw,blood work,imaging,mri,ct scan,xray,ultrasound,radiology,radiology imaging,quest imaging,physical therapy,pt clinic,sports medicine,chiropractor,chiropractic,acupuncture,massage therapy,massage,pt,physical therapist,occupational therapy,ot,speech therapy,st,home health,home care,audiologist,hearing aid,therapy,therapist,counselor,counseling,psychologist,psychiatrist,mental health,psych,psychotherapy,psychology,therapist office,lab test,blood test,urine test,stool test,therapy session,medicare,medicaid,aetna,united healthcare,blue cross,blue shield,cigna,humana,anthem,health net,molina healthcare,molina,pharmacy benefit manager,pbm,express scripts,optumrx,caremark,cvs caremark,prescription drugs,insulin,epi pen,prescription refill,dental insurance,vision insurance,health insurance,co pay,copay,deductible,premium,health savings account,hsa,fsa,flexible spending,urgent care center,telemedicine,teladoc,amwell,doctor on demand,lab draw station,blood lab,diagnostic lab,mra,mri center,imaging center,breast imaging,mammogram,pet scan,ct imaging,dental hygienist,teeth cleaning,root canal,filling,crown,bridge,dental implant,braces,invisalign,eye exam,glasses prescription,contact lens fitting,cataract surgery,lasik surgery,vet visit,pet meds,flea meds,heartworm,spay neuter,pharmacy benefit,drug store pharmacy,drive thru pharmacy'),
            ('Housing', 'expense', 'rent,rental,rent payment,apartment rent,apt rent,lease,lease payment,landlord,mortgage,mortgage payment,home loan,escrow,zillow rent,zillow,rent.com,apartments.com,craigslist rent,property management,pmi,hoa,homeowners association,condo association,co-op fee,maintenance fee,property tax,property taxes,real estate tax,real estate taxes,home insurance,homeowners insurance,renters insurance,home warranty,property insurance,landlord insurance,maintenance,home repair,home maintenance,plumbing,electrician,hvac,air conditioning,heating,roof repair,landscaping,lawn care,exterminator,pest control,house cleaning,maid service,janitorial,cleaning service,home services,handyman,contractor,general contractor,roofing,siding,windows,doors,gutter cleaning,pool service,pool maintenance,spa service,hot tub,security system,alarm monitoring,adt,vivint,frontpoint,home security,smart home,ring doorbell,nest,google nest,amazon ring,utilities deposit,security deposit,pet deposit,late fee,nsf fee,eviction fee,first month rent,last month rent,prorated rent,pet rent,parking rent,storage rent,garage rent,boat slip,marina slip,timeshare,timeshare fee,vacation rental,airbnb,vrooom,vrbo,homeaway,property manager,leasing office,leasing agent,tenant screening,credit check rent,background check rent,eviction screening,pet screening'),
            ('Salary', 'income', 'salary,paycheck,wage,pay,employment,payroll'),
            ('Investment', 'income', 'dividend,interest,investment'),
            ('Other Income', 'income', ''),
            ('Other Expense', 'expense', '')
        ]

        # Insert sensible default categories (idempotent via INSERT OR IGNORE)
        for name, cat_type, keywords in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type, keywords)
                VALUES (?, ?, ?)
            ''', (name, cat_type, keywords))
    
    def add_transaction(self, date: str, description: str, amount: int, 
                       category_id: int = None, account_id: int = None, 
                       transaction_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (date, description, amount, category_id, account_id, transaction_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, description, amount, category_id, account_id, transaction_type, notes))
        
        # Return the new transaction id for caller convenience
        conn.commit()
        transaction_id = cursor.lastrowid
        conn.close()
        return transaction_id
    
    def get_transactions(self, start_date: str = None, end_date: str = None, 
                        category_id: int = None, account_id: int = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, c.name AS category_name, a.name AS account_name 
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN accounts a ON t.account_id = a.id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND t.date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND t.date <= ?'
            params.append(end_date)
        if category_id:
            query += ' AND t.category_id = ?'
            params.append(category_id)
        if account_id:
            query += ' AND t.account_id = ?'
            params.append(account_id)
        
        query += ' ORDER BY t.date DESC'
        
        # Execute parameterized query and return list of dicts (column name -> value)
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return transactions
    
    def update_transaction(self, transaction_id: int, date: str, description: str, 
                      amount: int, category_id: int, account_id: int, transaction_type: str, notes: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transactions 
            SET date = ?, description = ?, amount = ?, category_id = ?, account_id = ?, transaction_type = ?, notes = ?
            WHERE id = ?
        ''', (date, description, amount, category_id, account_id, transaction_type, notes, transaction_id))
    
        conn.commit()
        conn.close()
    
    def delete_transaction(self, transaction_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        conn.commit()
        conn.close()
    
    def add_category(self, name: str, cat_type: str, keywords: str = ''):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO categories (name, type, keywords) VALUES (?, ?, ?)',
                      (name, cat_type, keywords))
        conn.commit()
        conn.close()

    def update_category(self, category_id: int, name: str, cat_type: str, keywords: str = ''):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE categories SET name = ?, type = ?, keywords = ? WHERE id = ?',
                           (name, cat_type, keywords, category_id))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            raise
        conn.close()

    def delete_category(self, category_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
    
    def get_categories(self, cat_type: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if cat_type:
            cursor.execute('SELECT * FROM categories WHERE type = ?', (cat_type,))
        else:
            cursor.execute('SELECT * FROM categories')
        
        columns = [description[0] for description in cursor.description]
        categories = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def get_category_totals_by_type(self, start_date: str = None, end_date: str = None, type: str = 'expense') -> Dict[str, float]:
        conn = self.get_connection()
        cursor = conn.cursor()
        # 1. Use LEFT JOIN so transactions without a category are included
        # 2. Use COALESCE to provide a display name for NULL category_ids
        query = '''
            SELECT 
                COALESCE(c.name, 'Uncategorized') as cat_name, 
                SUM(t.amount) as total
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE (c.type = ? OR t.category_id IS NULL)
        '''
        params = [type]

        if start_date:
            query += ' AND t.date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND t.date <= ?'
            params.append(end_date)

        query += ' GROUP BY cat_name'

        cursor.execute(query, params)
        
        # Store results in a dictionary { 'Groceries': 450.0, 'Dining': 120.0 }
        totals = {row[0]: abs(row[1]) for row in cursor.fetchall()}

        conn.close()
        return totals
    
    def add_account(self, name: str, account_type: str, create_template: bool = True):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Create the account
            cursor.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', (name, account_type))
            
            # 2. Create the linked asset template using the ID
            if create_template:
                cursor.execute('''
                    INSERT INTO asset_templates (asset_name, asset_type, notes) 
                    VALUES (?, ?, 'Added automatically during account creation')
                ''', (name, account_type))
            
            conn.commit()
        except sqlite3.IntegrityError:
            print(f"Account {name} already exists.")
        finally:
            conn.close()

    def delete_account(self, account_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
    
    def update_account(self, account_id: int, name: str, account_type: str,):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE accounts SET name = ?, type = ?, last_updated = ?
                WHERE id = ?
            ''', (name, account_type.lower(), datetime.now().isoformat(), account_id))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            raise
        conn.close()
    
    def get_accounts(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts')
        columns = [description[0] for description in cursor.description]
        accounts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return accounts

    def add_asset_template(self, asset_name: str, asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO asset_templates (asset_name, asset_type, notes)
            VALUES (?, ?, ?)
        ''', (asset_name, asset_type, notes))
        conn.commit()
        conn.close()

    def get_asset_templates(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM asset_templates ORDER BY asset_name')
        columns = [description[0] for description in cursor.description]
        templates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return templates

    def update_asset_template(self, template_id: int, asset_name: str, asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE asset_templates
            SET asset_name = ?, asset_type = ?, notes = ?
            WHERE id = ?
        ''', (asset_name, asset_type, notes, template_id))
        conn.commit()
        conn.close()

    def delete_asset_template(self, template_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM asset_templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()

    def apply_templates_to_month(self, year: int, month: int, template_values: Dict[int, float]):
        from calendar import monthrange
        start_date = f"{year}-{month:02d}-01"
        last_day = monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day:02d}"

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT asset_name FROM net_worth_entries
            WHERE date >= ? AND date <= ?
        ''', (start_date, end_date))
        existing_assets = {row[0] for row in cursor.fetchall()}

        templates = self.get_asset_templates()

        for template in templates:
            if template['asset_name'] not in existing_assets and template['id'] in template_values:
                cursor.execute('''
                    INSERT INTO net_worth_entries (date, asset_name, asset_type, value, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (start_date, template['asset_name'], template['asset_type'],
                      template_values[template['id']], template['notes']))

        conn.commit()
        conn.close()
    
    def add_net_worth_entry(self, date: str, asset_name: str, value: int,
                           asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO net_worth_entries (date, asset_name, asset_type, value, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, asset_name, asset_type, value, notes))

        conn.commit()
        conn.close()

    def update_net_worth_entry(self, entry_id: int, date: str, asset_name: str, value: int,
                              asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE net_worth_entries
            SET date = ?, asset_name = ?, asset_type = ?, value = ?, notes = ?
            WHERE id = ?
        ''', (date, asset_name, asset_type, value, notes, entry_id))
        conn.commit()
        conn.close()

    def get_net_worth_entries(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM net_worth_entries WHERE 1=1'
        params = []

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        query += ' ORDER BY date ASC'

        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        entries = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return entries

    def delete_net_worth_entry(self, entry_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM net_worth_entries WHERE id = ?', (entry_id,))
        conn.commit()
        conn.close()

    def get_net_worth_summary(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        conn = self.get_connection()
        cursor = conn.cursor()

        if not start_date:
            start_date = '1900-01-01'
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        query = '''
            SELECT asset_type, SUM(value) as total
            FROM (
                SELECT asset_name, asset_type, value
                FROM net_worth_entries e1
                WHERE date = (
                    SELECT MAX(date)
                    FROM net_worth_entries e2
                    WHERE e2.asset_name = e1.asset_name
                    AND e2.date >= ?
                    AND e2.date <= ?
                )
                GROUP BY asset_name
            )
            GROUP BY asset_type
        '''

        cursor.execute(query, (start_date, end_date))

        summary = {row[0] or 'Other': row[1] for row in cursor.fetchall()}
        conn.close()
        return summary

    def get_net_worth_history(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT strftime('%Y-%m', date) AS month
            FROM net_worth_entries
            ORDER BY month
        ''')

        months = [row[0] for row in cursor.fetchall()]

        if not months or not months[0]:
            return []
        
        history = []

        for month in months:
            year, month_num = month.split('-')
            start_date = f"{year}-{month_num}-01"

            if month_num == '12':
                end_date = f"{year}-12-31"
            else:
                last_day = 31
                if month_num in ['04', '06', '09', '11']:
                    last_day = 30
                elif month_num == '02':
                    last_day = 29 if int(year) % 4 == 0 and (int(year) % 100 != 0 or int(year) % 400 == 0) else 28
                end_date = f"{year}-{month_num}-{last_day}"

            summary = self.get_net_worth_summary(start_date, end_date)
            total = sum(summary.values())

            history.append({
                'month': month,
                'total': total,
                'breakdown': summary
            })

        conn.close()
        return history

    def add_budget_target(self, category_id: int, monthly_target: int, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO budget_targets (category_id, monthly_target, notes)
            VALUES (?, ?, ?)
        ''', (category_id, monthly_target, notes))
        conn.commit()
        conn.close()

    def get_all_category_budgets(self, cat_type: str = 'expense') -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        # Filter by the category type ('income' or 'expense')
        cursor.execute('''
            SELECT 
                c.id AS category_id, 
                c.name AS category_name, 
                b.id AS budget_id, 
                COALESCE(b.monthly_target, 0) AS monthly_target, 
                b.notes 
            FROM categories c
            LEFT JOIN budget_targets b ON c.id = b.category_id
            WHERE c.type = ?
            ORDER BY c.name
        ''', (cat_type,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_budget_targets(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        # Join with the categories table to get the name for the UI
        cursor.execute('''
            SELECT b.id, b.category_id, c.name, b.monthly_target, b.notes 
            FROM budget_targets b
            JOIN categories c ON b.category_id = c.id
            ORDER BY c.name
        ''')

        budgets = []
        for row in cursor.fetchall():
            budgets.append({
                'id': row[0],
                'category_id': row[1],
                'category_name': row[2],
                'monthly_target': row[3],
                'notes': row[4]
            })
        
        conn.close()
        return budgets

    def update_budget_target(self, budget_id: int, category_id: int, monthly_target: int, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE budget_targets SET category_id = ?, monthly_target = ?, notes = ?
            WHERE id = ?
        ''', (category_id, monthly_target, notes, budget_id))
        conn.commit()
        conn.close()

    def delete_budget_target(self, budget_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budget_targets WHERE id = ?', (budget_id,))
        conn.commit()
        conn.close()

    def add_import_template(self, template_name: str, account_id: int, date_column: str,
                           description_column: str, amount_column: str = None, skip_rows: int = 0, notes: str = None,
                           debit_column: str = None, credit_column: str = None,
                           description2_column: str = None, description_delimiter: str = ' - '):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO import_templates (template_name, account_id, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (template_name, account_id, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes))
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return template_id

    def get_import_templates(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                it.*, 
                a.name AS account_name
            FROM import_templates it
            JOIN accounts a ON it.account_id = a.id
            ORDER BY a.name
        ''')

        columns = [description[0] for description in cursor.description]
        templates = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return templates

    def get_import_template(self, template_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        # We join with the accounts table so the UI knows which 
        # human-readable account this template belongs to.
        cursor.execute('''
            SELECT 
                it.*, 
                a.name AS account_name
            FROM import_templates it
            JOIN accounts a ON it.account_id = a.id
            WHERE it.id = ?
        ''', (template_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            # We use the column description to map results to a dictionary
            # This makes the method resilient to future column additions.
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
            
        return None

    def update_import_template(self, template_id: int, template_name: str, account_id: int,
                              date_column: str, description_column: str, amount_column: str = None,
                              skip_rows: int = 0, notes: str = None, debit_column: str = None, 
                              credit_column: str = None, description2_column: str = None, 
                              description_delimiter: str = ' - '):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE import_templates
            SET template_name = ?, account_id = ?, date_column = ?, description_column = ?, 
                description2_column = ?, description_delimiter = ?, amount_column = ?, 
                debit_column = ?, credit_column = ?, skip_rows = ?, notes = ?
            WHERE id = ?
        ''', (template_name, account_id, date_column, description_column, 
            description2_column, description_delimiter, amount_column, 
            debit_column, credit_column, skip_rows, notes, template_id))
        conn.commit()
        conn.close()

    def delete_import_template(self, template_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM import_templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()

    def add_description_rule(self, template_id: int, rule_order: int, pattern: str,
                            replacement: str, category_id: int = None, ignore: int = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Automatically find the next order index
        cursor.execute('SELECT COALESCE(MAX(rule_order), -1) + 1 FROM description_rules WHERE template_id = ?', (template_id,))
        next_order = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO description_rules (template_id, rule_order, pattern, replacement, category_id, ignore)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_id, next_order, pattern, replacement, category_id, ignore))
        
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rule_id

    def get_description_rules(self, template_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        # Join with categories to get the human-readable name for the UI
        query = '''
            SELECT r.*, c.name as category_name 
            FROM description_rules r
            LEFT JOIN categories c ON r.category_id = c.id
            WHERE r.template_id = ? 
            ORDER BY r.rule_order ASC
        '''
        
        cursor.execute(query, (template_id,))
        columns = [desc[0] for desc in cursor.description]
        rules = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return rules

    def update_description_rule(self, rule_id: int, rule_order: int, pattern: str,
                               replacement: str, category_id: int, ignore: int = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE description_rules
            SET rule_order = ?, pattern = ?, replacement = ?, category_id = ?, ignore = ?
            WHERE id = ?
        ''', (rule_order, pattern, replacement, category_id, ignore, rule_id))
        conn.commit()
        conn.close()

    def delete_description_rule(self, rule_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Get the template_id and rule_order of the rule being deleted
        cursor.execute('SELECT template_id, rule_order FROM description_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        
        if row:
            template_id, deleted_order = row
            
            # Delete the rule
            cursor.execute('DELETE FROM description_rules WHERE id = ?', (rule_id,))
            
            # Shift all subsequent rules down by 1
            cursor.execute('''
                UPDATE description_rules 
                SET rule_order = rule_order - 1 
                WHERE template_id = ? AND rule_order > ?
            ''', (template_id, deleted_order))
        conn.commit()
        conn.close()

    def reorder_description_rules(self, template_id: int, rule_ids_in_order: List[int]):
        conn = self.get_connection()
        cursor = conn.cursor()
        for order, rule_id in enumerate(rule_ids_in_order):
            cursor.execute('UPDATE description_rules SET rule_order = ? WHERE id = ?', (order, rule_id))
        conn.commit()
        conn.close()

    # ID helper functions
    def get_category_id_by_name(self, name: str, cat_type: str = 'expense', create_if_missing: bool = True) -> Optional[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM categories WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if row:
            category_id = row[0]
        else:
            category_id = None
        
        '''
        elif create_if_missing:
            # Create it on the fly if it doesn't exist
            cursor.execute('INSERT INTO categories (name, type) VALUES (?, ?)', (name, cat_type))
            conn.commit()
            category_id = cursor.lastrowid
        '''
            
        conn.close()
        return category_id
    
    def get_category_name_by_id(self, id: int) -> Optional[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM categories WHERE id = ?', (id,))
        row = cursor.fetchone()
        
        if row:
            category_name = row[0]
        else:
            category_name = None
            
        conn.close()
        return category_name

    def get_account_id_by_name(self, name: str, account_type: str = 'checking', create_if_missing: bool = True) -> Optional[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM accounts WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if row:
            account_id = row[0]
        else:
            account_id = None
        '''
        elif create_if_missing:
            cursor.execute('INSERT INTO accounts (name, type) VALUES (?, ?)', (name, account_type))
            conn.commit()
            account_id = cursor.lastrowid
        '''
            
        conn.close()
        return account_id
    
    def get_account_name_by_id(self, id: int) -> Optional[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM accounts WHERE id = ?', (id,))
        row = cursor.fetchone()
        
        if row:
            account_name = row[0]
        else:
            account_name = None
            
        conn.close()
        return account_name
