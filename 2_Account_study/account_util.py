import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

map_color = {'Provax':'#00CC96','Novax':'#EF553B','Link low credibility':'#FF6692','Not defined':'#636EFA'}

def add_user_type(df,listNovax,listProvax,listLinklow):
    df['user_type'] = 'Not defined'
    for u in df.index:
        df.at[u,'user_type'] = 'Novax' if u in listNovax else df.at[u,'user_type']
        df.at[u,'user_type'] = 'Provax' if u in listProvax else df.at[u,'user_type']
        df.at[u,'user_type'] = 'Link low credibility' if u in listLinklow else df.at[u,'user_type']
    return df

def print_histogram_users(df,num_users,col_x,graph_title,col_x_title):
    fig = go.Figure()
    if num_users>25:
        n = num_users//2
        fig = px.histogram(df.head(num_users-n), y = df.head(num_users-n).index, x=col_x
                           ,color='user_type',orientation='h',color_discrete_map=map_color)
        fig.update_layout(title= graph_title + "(first %d)"%(num_users-n),
                          legend_title_text='User type')
        fig.update_yaxes(title='Username')
        fig.update_xaxes(title=col_x_title)
        fig.update_yaxes(categoryorder='total descending')
        fig.show()
        
        fig = px.histogram(df.head(num_users).tail(n), y = df.head(num_users).tail(n).index,
                           x=col_x,color='user_type',orientation='h',color_discrete_map=map_color)
        fig.update_layout(title=graph_title + "(first %d)"%(n),legend_title_text='User type')
    
    else:
        fig = px.histogram(df.head(num_users),y=df.head(num_users).index,x=col_x,orientation='h'
                           ,color='user_type',color_discrete_map=map_color)
        fig.update_layout(title=graph_title)
        
    fig.update_xaxes(title=col_x_title)
    fig.update_yaxes(title="Username")
    fig.update_yaxes(categoryorder='total descending')
    fig.show()


def get_df_raggruped (df,name_col,name_groupby):
    dfReturn = df
    dfReturn[name_col] = 1
    dfReturn = dfReturn.groupby(name_groupby).sum()
    dfReturn = dfReturn.loc[:,dfReturn.columns[dfReturn.columns.str.contains('id', regex=False)==False]]

    dfReturn.sort_values([name_col],axis = 0,inplace=True,ascending=False)

    for col in df.columns:
        if df[col].dtype==bool:
            dfReturn[col] = dfReturn[col]>0 if 1 else 0
            
    return dfReturn