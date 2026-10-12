"""
CineMithresh - Database Seed Script
Populates movies catalog, screens, seat layouts, showtimes, snacks, coupons, initial reviews and demo users.
"""

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from database import Database, init_database
from config import media_url

def seed_database():
    init_database()

    # 1. Seed Demo Users
    existing_user = Database.query_one("SELECT id FROM users WHERE email = %s", ('mithresh@cinemithresh.com',))
    if not existing_user:
        hashed_pw = generate_password_hash('Mithresh@2026')
        Database.execute("""
            INSERT INTO users (name, email, password_hash, phone, role, cine_points)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Mithresh P', 'mithresh@cinemithresh.com', hashed_pw, '+91 99440 12345', 'admin', 500))

    # Also seed a regular test member
    existing_member = Database.query_one("SELECT id FROM users WHERE email = %s", ('member@example.com',))
    if not existing_member:
        hashed_pw = generate_password_hash('Member@123')
        Database.execute("""
            INSERT INTO users (name, email, password_hash, phone, role, cine_points)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Rahul Sharma', 'member@example.com', hashed_pw, '+91 98765 43210', 'customer', 200))

    # 2. Seed Screens
    screens_data = [
        (1, "Mithresh IMAX Laser - Screen 1", "4K Dual Laser & 12-Track Audio", 80),
        (2, "Mithresh Dolby Atmos - Audi 2", "64 Discrete Surround Channels", 80),
        (3, "Mithresh VIP Lounge - Screen 3", "Plush Motorized Recliners & Gourmet Delivery", 80)
    ]
    for s_id, s_name, s_feat, s_seats in screens_data:
        existing = Database.query_one("SELECT id FROM screens WHERE id = %s", (s_id,))
        if not existing:
            Database.execute("""
                INSERT INTO screens (id, name, features, total_seats)
                VALUES (%s, %s, %s, %s)
            """, (s_id, s_name, s_feat, s_seats))

    # 3. Seed Seat Definitions (Rows A to H, 10 seats each)
    seat_layout = [
        ('A', 'VIP', 350.0, 1),
        ('B', 'VIP', 350.0, 1),
        ('C', 'Platinum', 220.0, 0),
        ('D', 'Platinum', 220.0, 0),
        ('E', 'Platinum', 220.0, 0),
        ('F', 'Gold', 150.0, 0),
        ('G', 'Gold', 150.0, 0),
        ('H', 'Gold', 150.0, 0)
    ]
    for row_label, tier, price, is_vip in seat_layout:
        for num in range(1, 11):
            seat_id = f"{row_label}{num}"
            existing = Database.query_one("SELECT id FROM seat_definitions WHERE id = %s", (seat_id,))
            if not existing:
                Database.execute("""
                    INSERT INTO seat_definitions (id, row_label, seat_number, tier, price, is_vip)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (seat_id, row_label, num, tier, price, is_vip))

    # 4. Seed Movies
    movies_data = [
        ('pushpa-2', 'Pushpa 2: The Rule', 'Action / Crime Thriller', 'Telugu / Tamil / Hindi', 8.9, '110K', '3h 15m', 'UA 16+', './pushpa_2.jpg', './pushpa_2.jpg',
         'Pushpa Raj asserts his iron-fisted dominion over the red sanders smuggling syndicate while facing the vengeful wrath of SP Bhanwar Singh Shekhawat in an explosive showdown.',
         'Allu Arjun, Rashmika Mandanna, Fahadh Faasil, Sunil', 'Sukumar', 'https://www.youtube.com/embed/g3JUbgOHgdw', 'IMAX • 4DX • Dolby Atmos 7.1', 'now_showing'),

        ('deadpool-wolverine', 'Deadpool & Wolverine', 'Action / Comedy / Superhero', 'English / Tamil / Hindi', 8.6, '145K', '2h 08m', 'A', './deadpool_wolverine.jpg', './deadpool_wolverine.jpg',
         'The Time Variance Authority pulls Wade Wilson from his peaceful civilian life, uniting him with a reluctant, battle-hardened Wolverine to save his home universe.',
         'Ryan Reynolds, Hugh Jackman, Emma Corrin, Matthew Macfadyen', 'Shawn Levy', 'https://www.youtube.com/embed/73_1biulkYk', 'IMAX 3D • 4DX • Dolby Atmos', 'now_showing'),

        ('coolie', 'Coolie', 'Action / Crime Thriller', 'Tamil / Telugu / Hindi', 8.8, '75.6K', '2h 45m', 'UA', './coolie_movie.jpg', './coolie_movie.jpg',
         'Superstar Rajinikanth takes on a ruthless gold smuggling cartel with unmatched swagger, razor-sharp action sequences, and high-voltage Anirudh background score.',
         'Rajinikanth, Nagarjuna, Soubin Shahir, Shruti Haasan, Upendra', 'Lokesh Kanagaraj', 'https://www.youtube.com/embed/qLcx3hL1i1A', 'IMAX • Dolby Atmos 7.1 • 4K Laser', 'now_showing'),

        ('goat', 'The Greatest of All Time (GOAT)', 'Action / Sci-Fi Thriller', 'Tamil / Telugu / Hindi', 8.3, '84.2K', '2h 59m', 'UA 13+', './goat_movie.jpg', './goat_movie.jpg',
         'An elite hostage negotiator and field operative of the Special Anti-Terrorist Squad confronts an enigmatic clone adversary tied to a clandestine mission.',
         'Thalapathy Vijay, Prashanth, Prabhu Deva, Sneha, Meenakshi Chaudhary', 'Venkat Prabhu', 'https://www.youtube.com/embed/jxCRlebieWc', 'IMAX • Dolby Atmos 7.1 • 2D', 'now_showing'),

        ('kalki-2898', 'Kalki 2898 AD', 'Sci-Fi / Epic Fantasy', 'Telugu / Tamil / Hindi', 8.7, '98.5K', '3h 01m', 'UA', './kalki_2898.jpg', './kalki_2898.jpg',
         'In a dystopian post-apocalyptic future ruled by Supreme Yaskin, the legendary Ashwatthama awakens to protect the carrier of the divine tenth avatar of Vishnu.',
         'Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone', 'Nag Ashwin', 'https://www.youtube.com/embed/y1-w1pU_S8o', 'IMAX 3D • Dolby Atmos • 4K Laser', 'now_showing'),

        ('spider-man', 'Spider-Man: Brand New Day', 'Action / Sci-Fi / Superhero', 'English / Tamil / Hindi', 8.8, '68.4K', '2h 18m', 'UA 13+', './spider_man.jpg', './spider_man.jpg',
         'Peter Parker embarks on a high-stakes adventure swinging through New York City as he confronts emerging threats and protects those who matter most.',
         'Tom Holland, Zendaya, Jacob Batalon', 'Destin Daniel Cretton', 'https://www.youtube.com/embed/rt-2cxAiGoI', 'IMAX 3D • 4DX • Dolby Atmos', 'now_showing'),

        ('demon-slayer', 'Demon Slayer: Infinity Castle I', 'Anime / Action / Fantasy', 'Japanese / English / Hindi', 9.1, '92.3K', '2h 10m', 'UA 16+', './demon_slayer.jpg', './demon_slayer.jpg',
         'Tanjiro Kamado, the Hashira, and the Demon Slayer Corps plunge headlong into the shifting multidimensional fortress of the Infinity Castle for the ultimate battle against Muzan Kibutsuji.',
         'Natsuki Hanae, Akari Kito, Hiro Shimono, Takahiro Sakurai', 'Haruo Sotozaki', 'https://www.youtube.com/embed/1Q_pUo1-zZc', '4K Laser • Dolby Atmos 7.1 • IMAX', 'now_showing'),

        ('viswanath-and-sons', 'Viswanath & Sons', 'Family Drama / Emotional Thriller', 'Tamil / Telugu', 8.5, '33.8K', '2h 30m', 'U', './viswanath_and_sons.jpg', './viswanath_and_sons.jpg',
         'An intense London-to-Tamil Nadu journey tracing three generations of familial bonds, corporate legacy conflicts, and heartfelt emotional reconciliations.',
         'Suriya, Pooja Hegde, Prakash Raj, Nassar', 'Venky Atluri', 'https://www.youtube.com/embed/Z0oY3i5YdKw', '2D • Dolby Atmos 7.1 • 4K Laser', 'now_showing'),

        ('vvan', 'VVAN: Force of the Forrest', 'Mythological Thriller / Action', 'Hindi / Tamil / Telugu', 8.4, '24.1K', '2h 22m', 'UA', './vvan.jpg', './vvan.jpg',
         'A mystical forest steeped in primeval folklore awakens when encroachers ignite the wrath of ancient guardians defending a sacred temple of flames.',
         'Sidharth Malhotra, Tamannaah Bhatia, Sara Ali Khan', 'Deepak Mishra', 'https://www.youtube.com/embed/9G3eW-n5jZc', '2D • Dolby Atmos 7.1', 'now_showing'),

        ('the-paradise', 'The Paradise', 'Action / Period Drama', 'Telugu / Tamil / Hindi', 8.6, '39.7K', '2h 35m', 'A', './paradise.jpg', './paradise.jpg',
         'Natural Star Nani stars as a fierce tribal champion waging a war of retribution against feudal exploiters in an uncompromising, raw period action spectacle.',
         'Nani, Janhvi Kapoor, Shine Tom Chacko', 'Srikanth Odela', 'https://www.youtube.com/embed/K8v9v-Y5t78', '2D • Dolby Atmos 7.1', 'now_showing'),

        ('agatha', 'Agatha', 'Supernatural Horror / Mystery', 'Telugu / Tamil', 7.9, '15.6K', '2h 08m', 'A', './agatha.jpg', './agatha.jpg',
         'An occult mystery set within a remote heritage mansion uncovers ancient dark rituals, cursed apparitions, and chilling psychological dread.',
         'Avika Gor, MS Raju, Sumanth Ashwin', 'MS Raju', 'https://www.youtube.com/embed/H0d6w4lE5bE', '2D • Dolby Atmos 7.1', 'now_showing'),

        ('godzilla-kong', 'Godzilla x Kong: The New Empire', 'Action / Sci-Fi', 'English / Tamil / Hindi', 8.2, '56.1K', '1h 55m', 'UA 13+', './movie4.jpg', './movie4.jpg',
         'Kong discovers a hidden tribe of apes in Hollow Earth ruled by the ruthless Skar King, forcing him to team up with the radioactive titan Godzilla.',
         'Rebecca Hall, Brian Tyree Henry, Dan Stevens, Kaylee Hottle', 'Adam Wingard', 'https://www.youtube.com/embed/lV1OOlGwExM', 'IMAX 3D • 4DX • Dolby Atmos', 'now_showing'),

        ('manjummel-boys', 'Manjummel Boys', 'Survival / Thriller', 'Malayalam / Tamil', 8.7, '42.9K', '2h 15m', 'U', './movie2.jpg', './movie6.jpg',
         'A tight-knit gang of friends from Kochi travel to Kodaikanal for a holiday, where one of them tragically slips into the pitch-black abyss of Guna Caves.',
         'Soubin Shahir, Sreenath Bhasi, Balu Varghese, Ganapathi', 'Chidambaram', 'https://www.youtube.com/embed/rQn0_E3u5-0', '2D • 4K Laser • Dolby Atmos', 'now_showing'),

        ('aranmanai-4', 'Aranmanai 4', 'Horror / Comedy', 'Tamil', 7.8, '18.4K', '2h 28m', 'UA', './movie1.jpg', './movie7.jpg',
         'A suspicious death in an isolated village leads an advocate brother to investigate a sinister entity called Baak lurking within a haunted ancestral palace.',
         'Sundar C, Tamannaah Bhatia, Raashii Khanna, Santhosh Prathap', 'Sundar C.', 'https://www.youtube.com/embed/5U2f4b4A_l8', '2D • Dolby Atmos 7.1', 'now_showing'),

        ('bad-boys', 'Bad Boys: Ride or Die', 'Action / Comedy', 'English / Tamil', 8.0, '31.2K', '1h 55m', 'A', './movie5.jpg', './movie5.jpg',
         'Miami narcotics detectives Mike Lowrey and Marcus Burnett fight to clear the posthumous name of Captain Conrad Howard when he is falsely accused.',
         'Will Smith, Martin Lawrence, Vanessa Hudgens, Alexander Ludwig', 'Adil El Arbi, Bilall Fallah', 'https://www.youtube.com/embed/hRFY_Fesa98', '2D • Dolby Atmos 7.1', 'now_showing')
    ]

    for m in movies_data:
        existing = Database.query_one("SELECT id FROM movies WHERE id = %s", (m[0],))
        if not existing:
            # Resolve poster/backdrop (indices 8 & 9) to external CDN URLs
            record = list(m)
            record[8] = media_url(record[8])
            record[9] = media_url(record[9])
            Database.execute("""
                INSERT INTO movies (id, title, genre, language, rating, votes, duration, certificate, poster, backdrop, synopsis, cast, director, trailer_url, formats, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(record))

    # 5. Seed Shows (for 5 days: Today, Tmrw, etc.)
    show_times = ['10:00 AM', '01:30 PM', '05:00 PM', '08:30 PM', '11:15 PM']
    now = datetime.now()
    days_list = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Generate dates for 5 days
    date_labels = []
    for i in range(5):
        d = now + timedelta(days=i)
        day_name = 'Today' if i == 0 else ('Tmrw' if i == 1 else days_list[d.weekday()])
        label = f"{day_name}, {months_list[d.month - 1]} {d.day}"
        date_labels.append(label)

    # Seed shows for popular movies across screens
    top_movies = ['pushpa-2', 'deadpool-wolverine', 'coolie', 'goat', 'kalki-2898', 'spider-man', 'demon-slayer', 'viswanath-and-sons', 'godzilla-kong', 'manjummel-boys']
    for m_id in top_movies:
        for s_id in [1, 2, 3]:
            for date_str in date_labels:
                for t_str in show_times:
                    existing = Database.query_one("""
                        SELECT id FROM shows WHERE movie_id = %s AND screen_id = %s AND show_date = %s AND show_time = %s
                    """, (m_id, s_id, date_str, t_str))
                    if not existing:
                        Database.execute("""
                            INSERT INTO shows (movie_id, screen_id, show_date, show_time)
                            VALUES (%s, %s, %s, %s)
                        """, (m_id, s_id, date_str, t_str))

    # 6. Seed Snacks
    snacks_data = [
        ('popcorn', 'Caramel Popcorn', '🍿', 180.0),
        ('nachos', 'Loaded Nachos', '🧀', 140.0),
        ('coke', 'Chilled Coca-Cola', '🥤', 90.0),
        ('combo', 'Couple Combo Pack', '🍱', 320.0)
    ]
    for sn_id, sn_name, sn_icon, sn_price in snacks_data:
        existing = Database.query_one("SELECT id FROM snacks WHERE id = %s", (sn_id,))
        if not existing:
            Database.execute("""
                INSERT INTO snacks (id, name, icon, price)
                VALUES (%s, %s, %s, %s)
            """, (sn_id, sn_name, sn_icon, sn_price))

    # 7. Seed Coupons
    coupons_data = [
        ('MITHRESH20', 20.0, 1, '20% OFF Special Launch Discount'),
        ('CINE20', 20.0, 1, '20% OFF Cinema Lovers Offer'),
        ('BLOCKBUSTER15', 15.0, 1, '15% OFF Blockbuster Experience')
    ]
    for c_code, c_disc, c_active, c_desc in coupons_data:
        existing = Database.query_one("SELECT code FROM coupons WHERE code = %s", (c_code,))
        if not existing:
            Database.execute("""
                INSERT INTO coupons (code, discount_percent, is_active, description)
                VALUES (%s, %s, %s, %s)
            """, (c_code, c_disc, c_active, c_desc))

    # 8. Seed Initial Reviews
    initial_reviews = [
        ('rev-1', 'pushpa-2', 'Karthik Raja', 'karthik@example.com', 5, 'Allu Arjun gives a career-defining performance! The theater erupted with claps. Sound mixing in Dolby Atmos here at CineMithresh was ground shaking!', 24),
        ('rev-2', 'demon-slayer', 'Ananya Sharma', 'ananya@example.com', 5, 'UFOTABLE animation on the big screen is pure art! The Infinity Castle visual depth and acoustic sword clashes felt surreal. 10/10 must watch in IMAX!', 18),
        ('rev-3', 'deadpool-wolverine', 'Rohan Mehta', 'rohan@example.com', 5, 'Non-stop laughter and insane superhero action. Ryan Reynolds and Hugh Jackman have the best on-screen chemistry of the decade!', 15),
        ('rev-4', 'spider-man', 'Praveen Kumar', 'praveen@example.com', 5, 'Spectacular web-swinging action sequences and great emotional moments. The 4K laser projection clarity was razor sharp.', 12),
        ('rev-5', 'viswanath-and-sons', 'Senthil Nathan', 'senthil@example.com', 5, 'Suriya sir delivered an emotionally gripping masterclass. GV Prakash songs blend so beautifully with the storyline.', 9),
        ('rev-6', 'manjummel-boys', 'Vijay Shankar', 'vijay@example.com', 5, 'Cinematic masterpiece! The tension, the friendship, the climax gave goosebumps. Dolby Atmos audio was mindblowing!', 14)
    ]
    for r_id, m_id, u_name, u_email, r_val, r_comm, r_likes in initial_reviews:
        existing = Database.query_one("SELECT id FROM reviews WHERE id = %s", (r_id,))
        if not existing:
            Database.execute("""
                INSERT INTO reviews (id, movie_id, user_name, email, rating, comment, likes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (r_id, m_id, u_name, u_email, r_val, r_comm, r_likes))

    print("[+] Database initialized and seeded successfully!")

if __name__ == '__main__':
    seed_database()
