import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
 
Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    home = Column(String(250), nullable=False)
    away = Column(String(250), nullable=False)
    date = Column(Date, nullable=False)
    sport = Column(String(250), nullable=False)

class Play(Base):
    __tablename__ = 'plays'
    id = Column(Integer, primary_key=True)
    period = Column(Integer, nullable=False)
    time = Column(Float, nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    home_comment = Column(String(250))
    away_comment = Column(String(250))
    game_id = Column(Integer, ForeignKey('games.id'))
    game = relationship(Game)


class Storage(object):
    def __init__(self, engine):
        self.engine = engine
        Base.metadata.create_all(self.engine)
        self.db_session = sessionmaker(bind=engine)
        self.session = self.db_session()
    
    def get_game(self, home, away, date, sport):
        return self.session.query(Game).filter(Game.home==home, Game.away==away, Game.date==date, Game.sport==sport).first()
    
    def save_game(self, home, away, date, sport):
        new_game = self.get_game(home, away, date, sport)
        if not new_game:
            new_game = Game(home=home, away=away, date=date, sport=sport)
            self.session.add(new_game)
            self.session.commit()
        return new_game
    
    def save_play(self, period, time, home_score, away_score, home_comment, away_comment, game):
        play = Play(period=period, time=time, home_score=home_score, 
                    away_score=away_score, home_comment=home_comment,
                    away_comment=away_comment, game=game)
        self.session.add(play)
        self.session.commit()
