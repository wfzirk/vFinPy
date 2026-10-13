
# Python Includes
import tkinter as tk
from tkinter import ttk
import logging

# 3rd Party Includes
import matplotlib
matplotlib.use("TkAgg")  # safe backend for PyInstaller
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

#Project Includes
import apswSql as sql
from logging_manager import get_logger
log = get_logger(__name__)

def linechart(x_values, y_values, x_label="", y_label="", title="Line Chart"):

    plt.figure(100, figsize=(10, 6)) # 10 inches wide and 6 inches high
    plt.plot(x_values, y_values, marker='o', linestyle='-', color='b') # 'o' adds markers to points

    # Add labels and title for clarity
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid(True) # Add a grid for easier reading

    # Display the chart
    plt.show(block=False)
    return plt

def barchart(x_values, y_values, x_label="", y_label="", title="Bar Chart"):

    plt.figure(200, figsize=(10, 6)) # 10 inches wide and 6 inches high
    plt.bar(x_values, y_values, color='skyblue')

    # Add labels and title
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)

    # Display the chart
    plt.show(block=False)
    return plt
    
def piechart(items, labels="", title="Pie Chart"):

    # Create the pie chart
    plt.figure(300, figsize=(10, 6)) # 10 inches wide and 6 inches high
    plt.pie(items, labels=labels, autopct='%1.1f%%', startangle=90)

    # Ensure the plot is drawn as a circle
    plt.axis('equal')
    plt.legend(loc='upper right')
    # Add a title and display the plot
    plt.title(title)

    plt.show(block=False)
    return plt


class Charts:
    def __init__(self, parent, cls):   #  :, parent):
        self.winc = parent
        self.cls = cls
        '''
        self.winc = tk.Toplevel()
        self.winc.attributes("-toolwindow", True) 
        self.winc.wm_attributes("-topmost", True)
        #winc.geometry("300x350")  #width, height
        self.winc.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.winc.title("Charts")
        '''
        #self.parent = self.winc
        self.notebook = ttk.Notebook(self.winc)
        self.notebook.pack(pady=10, expand=True, fill='both')
        #print('cccccc',self.notebook)
        
    def on_closing(self):
        log.info('charts closing')
        self.cls()
        self.winc.destroy()
        


    #  Add the navigation toolbar (optional)
    def nav_tool_bar(self, canvas, tab):
        #  Add the navigation toolbar (optional)
        toolbar = NavigationToolbar2Tk(canvas, tab)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def chart_canvas(self, fig, tab):
        # Create a Tkinter canvas from the figure       
        self.canvas = FigureCanvasTkAgg(fig, master=tab)  # Embed in the specified frame
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    #def bar_chart(self, values, labels=""):
    def bar_chart(self, x_values, y_values, x_label="", y_label="", title="Bar Chart"):
        log.info('bar_chart')
        #print('bbbbbb',self.notebook)
        tab = ttk.Frame(self.notebook)
        tab.pack(fill='both', expand=True)
        self.notebook.add(tab, text='Bar Chart')
        
        # 1. configure x axis data
        x_pos = []
        y_val = []
        for x, v in enumerate(y_values):
            x_pos.append(x)
            y_val.append(v)

        # Create a figure object
        fig, ax = plt.subplots()
        ax.bar(x_values, y_values)
        # Set the tick locations
        #ax.set_xticks(x_pos)

        # Set the custom labels at those locations
        #ax.set_xticklabels(labels)
        
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label) # Optional: Add a y-axis label
        ax.set_title(title)    # Optional: Add a plot title
        
        self.chart_canvas(fig, tab)
        self.nav_tool_bar(self.canvas, tab)
        return ax
        
    def line_chart(self, x_values, y_values, x_label="", y_label="", title="Line Chart"):
        log.info('line_chart')
        #print('llllll',self.notebook)
        tab = ttk.Frame(self.notebook)
        tab.pack(fill='both', expand=True)
        self.notebook.add(tab, text='Line Chart')

        fig, ax = plt.subplots()
        #ax.plot(x_pos, y_val, label=lbl)
        #fig = plt.figure(333, figsize=(10, 6)) # 10 inches wide and 6 inches high
        #plt.figure(100, figsize=(10, 6)) # 10 inches wide and 6 inches high
        ax.plot(x_values, y_values, marker='o', linestyle='-', color='b') # 'o' adds markers to points

        # Add labels and title for clarity
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        plt.grid(True) # Add a grid for easier reading

        # Display the chart
        #plt.show(block=False)
        #ax.legend(loc='upper right')
        self.chart_canvas(fig, tab) 
        self.nav_tool_bar(self.canvas, tab)
        return ax

    def pie_chart(self, items, labels="", title="Pie Chart"):
        log.info('pie_chart')
        #print('pppppp',self.notebook)
        tab = ttk.Frame(self.notebook)
        tab.pack(fill='both', expand=True)
        self.notebook.add(tab, text='Pie Chart')
        
        # 2. Create a figure object
        #fig, ax = plt.subplots()
        #fig = plt.figure()
        
        fig = plt.figure(333, figsize=(10, 6)) # 10 inches wide and 6 inches high
        ax = fig.add_subplot(111)

        wedges, texts = ax.pie(items, labels=labels)   #, autopct='%1.1f%%') #, startangle=90) #, pctdistance=1.1, labeldistance=1.3)

        #p = plt.pie(fracs, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)
        #plt.title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})
    
        ax.set_title(title)
        ax.set_ylabel("Amount (%)")
        ax.axis('equal')  # Ensure the pie chart is drawn as a circle (prevents oval shape)
        ax.legend(loc='upper right')
        self.chart_canvas(fig, tab) 
        self.nav_tool_bar(self. canvas, tab)
        # Connect the pick event
        self.make_picker(fig, wedges)
        return ax
        
    def pie_chart_legend(self, items, labels="", title="Pie Chart"):
        log.info('pie_chart')
        #print('pppppp',self.notebook)
        tab = ttk.Frame(self.notebook)
        tab.pack(fill='both', expand=True)
        self.notebook.add(tab, text='Pie Chart')
        
        # 2. Create a figure object
        #fig, ax = plt.subplots()
        #fig = plt.figure()
        
        fig = plt.figure(333, figsize=(10, 6)) # 10 inches wide and 6 inches high
        ax = fig.add_subplot(111)

        wedges, texts = ax.pie(items, labels=labels)   #, autopct='%1.1f%%') #, startangle=90) #, pctdistance=1.1, labeldistance=1.3)

        #p = plt.pie(fracs, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)
        #plt.title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})
    
        ax.set_title(title)
        ax.set_ylabel("Amount (%)")
        ax.axis('equal')  # Ensure the pie chart is drawn as a circle (prevents oval shape)
        ax.legend(loc='upper right')
        self.chart_canvas(fig, tab) 
        self.nav_tool_bar(self. canvas, tab)
        # Connect the pick event
        self.make_picker(fig, wedges)
        return ax
        
    def make_picker(self, fig, wedges):
        """
        Sets each wedge as pickable and connects the pick_event to a handler.
        """
        # Make wedges selectable by setting a picker tolerance (e.g., True for a simple pick)
        for wedge in wedges:
            wedge.set_picker(True)

        # Connect the callback function to the 'pick_event'
        # The 'pick_event' is specific to an artist being picked, 
        # as opposed to a general 'button_press_event' on the canvas.
        fig.canvas.mpl_connect('pick_event', self.onclick)
        
    def onclick(self, event):
        """
        The callback function that handles the event when a wedge is clicked.
        """
        # The event object has an 'artist' attribute which is the picked wedge
        wedge = event.artist
        
        # Retrieve the label associated with the wedge
        # get_label() method returns the label string
        label = wedge.get_label()
        
        log.info(f"Get SubCAtegory of {label}")

        data, cols, err = sql.sqlQuery(f"SELECT SubCategory FROM transactions WHERE Category = '{label}';")
        
        scatcnt = {}
        if not err:
            for scat in data:
                if scat[0] in scatcnt:
                    scatcnt[scat[0]] += 1 
                else:
                    scatcnt[scat[0]]= 1
            
            #chrts = Charts(self.winc, self.cls)
            self.pie_chart(scatcnt.values(), labels=scatcnt.keys(), title=f"Sub Categories of {label}")
            #piechart(scatcnt.values(), labels=scatcnt.keys(), title=f"Sub Categories of {label}")
            
        
    
if __name__ == "__main__":
    import sys

    def on_close():
        sys.exit()
        
    '''data = [-7938.7699999999995, 1330.1199999999992, -19199.07, 1376.41, 1043.9299999, -923.8999999999979, -1384.930000000001, 1148.8500000000008, -574.1299999999984, -2264.139999999999, 198.00000000000034]

    columns = ["'2025-01'", "'2025-02'", "'2025-03'", "'2025-04'", "'2025-05'", "'2025-06'", "'2025-07'", "'2025-08'", "'2025-09'", "'2025-10'", "'2025-11'"]
    '''
    gv = [6943.44, 9561.0, -2107.34]
    columns = ('2023', '2024', '2025', 'Total')
    catcnt = {'Auto': 32, 'Charity': 35, 'Entertainment': 78, 'Financial': 54, 'Household': 148, 'Income': 19, 'Insurance': 9, 'Medical': 39, 'Travel': 78, 'Utility': 2}
    

    root = tk.Tk()
    root.title("Tkinter Notebook with Charts")
    root.geometry("800x600")
    root.protocol("WM_DELETE_WINDOW", on_close)

    
    chrts = Charts(root, on_close)
    chrts.line_chart(columns[:-1], gv)  #, x_label="Year", y_label="Amount", title="By Year")
    chrts.pie_chart(catcnt.values(), labels=catcnt.keys(), title="Categories")
    chrts.bar_chart(columns[:-1], gv, x_label="Year", y_label="Amount", title="By Year")

    
    root.mainloop()
