from Models_Fundaments import Models_Fundaments
import xgboost as xgb
import lightgbm as lgb
import catboost as cat
import pandas as pd
import numpy as np
from IPython.core.display import clear_output

class Models_for_Predictions(Models_Fundaments):
    '''Класс для предсказаний. Включает в себя три модели: xgb, lgb, cat. Опирается на класс Models_Fundaments. 
    Работает в двух режимах: val and test. Каждая модель возращает 2 результата предксказание по train и  test/val в зависимости от режима.
    '''
    

    def xgb_stacking(self, target=None,):
        

        X = self.train.drop(self.cols_to_drop, axis=1)
        y = self.train[target].values
 
        xgb_models =[]
        predict_train = []
        predict_test = []
        predict_val = []
        for fold, (train_ids, val_ids) in enumerate(self.folds.split(X,y)):
            dtrain = xgb.DMatrix(X.iloc[train_ids], y[train_ids])
            dval = xgb.DMatrix(X.iloc[val_ids], y[val_ids])
            model = xgb.train(params=self.xgb_params,
                                          dtrain=dtrain,
                                          evals=[(dtrain, 'train'), (dval, 'val')],
                                          verbose_eval=200,
                                          early_stopping_rounds=100
                                         )
            pred = model.predict(xgb.DMatrix(X.iloc[val_ids]))
            predict_train=np.concatenate([pred, predict_train])
            if self.mode == 'val':
               predict_val.append(model.predict(xgb.DMatrix(self.val.drop(self.cols_to_drop, axis=1))))
                
            if self.mode == 'test':
                
                predict_test.append(model.predict(xgb.DMatrix(self.test.drop(self.drop_columns_test, axis=1))))
                
            xgb_models.append(model)
        clear_output()
        if self.mode=='val':
            return predict_train, np.asarray(predict_val).mean(axis=0)
        if self.mode=='test':
            return predict_train, np.asarray(predict_test).mean(axis=0)



    def lgb_stacking(self, target=None):
        
        X = self.train.drop(self.cols_to_drop, axis=1)
        y = self.train[target].values

           
        lgb_models =[]
        predict_train = []
        predict_test = []
        predict_val = []
          
        for fold, (train_ids, val_ids) in enumerate(self.folds.split(X,y)):
            train_set = lgb.Dataset(X.iloc[train_ids], y[train_ids])
            val_set = lgb.Dataset(X.iloc[val_ids], y[val_ids])
            model = lgb.train(params=self.lgb_params,
                                                  train_set=train_set,
                                                  valid_sets=[train_set, val_set],
                                                  num_boost_round =2000,
                                                  verbose_eval=100,
                                                  early_stopping_rounds=100
                                                 )
            pred = model.predict((X.iloc[val_ids]), num_iteration=model.best_iteration)
            predict_train=np.concatenate([pred, predict_train])                             
           
            if self.mode == 'val':
                predict_val.append(model.predict((self.val.drop(self.cols_to_drop, axis=1)), num_iteration=model.best_iteration))
            
            if self.mode == 'test':
                predict_test.append(model.predict((self.test.drop(self.drop_columns_test, axis=1)), num_iteration=model.best_iteration))
               
            lgb_models.append(model)
        clear_output()    
        if self.mode=='val':
            return predict_train, np.asarray(predict_val).mean(axis=0)
        if self.mode=='test':
            return predict_train, np.asarray(predict_test).mean(axis=0)

    def cat_stacking(self, target=None,):

        X = self.train.drop(self.cols_to_drop, axis=1)
        y = self.train[target].values
            
        cat_models =[]
        predict_train = []
        predict_test = []
        predict_val = []
            
        for fold, (train_ids, val_ids) in enumerate(self.folds.split(X,y)):
            dtrain = cat.Pool(X.iloc[train_ids], y[train_ids])
            dval = cat.Pool(X.iloc[val_ids], y[val_ids])
            model = cat.train(params=self.cat_params,
                                      dtrain=dtrain,
                                      eval_set=dval,
                                      verbose=200,
                                      early_stopping_rounds=100
                                     )
                                                 
                                         
            pred = model.predict((cat.Pool(X.iloc[val_ids])))
            predict_train=np.concatenate([pred, predict_train])    
            if self.mode == 'val':
                
                
                predict_val.append(model.predict(cat.Pool(self.val.drop(self.cols_to_drop, axis=1))))
               
            if self.mode == 'test':
                predict_test.append(model.predict(cat.Pool(self.test.drop(self.drop_columns_test, axis=1))))
               
            cat_models.append(model)
        clear_output()    
        if self.mode=='val':
            return predict_train, np.asarray(predict_val).mean(axis=0)
        if self.mode=='test':
            return predict_train, np.asarray(predict_test).mean(axis=0)


    def upgrade_data(self, path,  mode='boost', save_file=None, xgb_target=None, lgb_target=None, cat_target=None):
        
        '''Функция для объединения предсказаний в и данных новый датафрейм для дальнейшей работы.
        Принимает в себя лист таргетов для каждой модели и делает для них предсказание. 
        Работает в двух режимах:
            boost - добавляет предсказания к исходным данным
            stack - формирует датафрейм из предсказаний.   
        Полученные датафреймы сохраняются в папку, затем подргужаются перевызовом класса'''
        
        all_predicts_train = []
        all_predicts_val_or_test = []
        if xgb_target != None:
            for target in xgb_target:
                xgb_predict_train, xgb_predict_val_or_test = self.xgb_stacking(target)
                all_predicts_train.append(xgb_predict_train)
                all_predicts_val_or_test.append(xgb_predict_val_or_test)
            
        if lgb_target != None:
            for target in lgb_target:
                lgb_predict_train, lgb_predict_val_or_test = self.lgb_stacking(target)
                all_predicts_train.append(lgb_predict_train)
                all_predicts_val_or_test.append(lgb_predict_val_or_test)
        if cat_target != None:
            for target in cat_target:
                cat_predict_train, cat_predict_val_or_test = self.cat_stacking(target)    
                all_predicts_train.append(cat_predict_train)
                all_predicts_val_or_test.append(cat_predict_val_or_test)
            
        if mode=='boost':
            
            self.train=pd.concat([self.train, pd.DataFrame(all_predicts_train).T], axis=1)
            if self.mode=='val':
                self.val = pd.concat([self.val, pd.DataFrame(all_predicts_val_or_test).T], axis=1)
                if save_file:
                    self.train.to_csv(path+'new_train.csv', index=False)
                    self.val.to_csv(path+'new_val.csv', index=False)
            if self.mode=='test':
                self.test = pd.concat([self.test, pd.DataFrame(all_predicts_val_or_test).T], axis=1)
                if save_file:
                    self.train.to_csv(path+'new_train.csv', index=False)
                    self.test.to_csv(path+'new_test.csv', index=False)
            
        elif mode == 'stack':
            self.new_train = pd.DataFrame(all_predicts_train).T
            if self.mode == 'val':
                self.new_val = pd.DataFrame(all_predicts_val_or_test).T
                if save_file:
                    self.train.to_csv(path+'new_train.csv', index=False)
                    self.val.to_csv(path+'new_val.csv', index=False)
            if self.mode == 'test':
                self.new_test = pd.DataFrame(all_predicts_val_or_test).T
                if save_file:
                    self.train.to_csv(path+'new_train.csv', index=False)
                    self.test.to_csv(path+'new_test.csv', index=False)
        
        
        

        


















                 
